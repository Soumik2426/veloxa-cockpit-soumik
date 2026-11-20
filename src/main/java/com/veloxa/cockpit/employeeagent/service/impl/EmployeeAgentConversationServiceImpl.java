package com.veloxa.cockpit.employeeagent.service.impl;

import java.math.BigDecimal;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;

import com.veloxa.cockpit.employeeagent.dto.AgentMessageResponse;
import com.veloxa.cockpit.employeeagent.dto.ConversationResponse;
import com.veloxa.cockpit.employeeagent.dto.CreateConversationRequest;
import com.veloxa.cockpit.employeeagent.dto.EmployeeAgentResponse;
import com.veloxa.cockpit.employeeagent.dto.SendAgentMessageRequest;
import com.veloxa.cockpit.employeeagent.dto.SendAgentMessageResponse;

import com.veloxa.cockpit.employeeagent.entity.AgentConversation;
import com.veloxa.cockpit.employeeagent.entity.AgentMemory;
import com.veloxa.cockpit.employeeagent.entity.AgentMessage;
import com.veloxa.cockpit.employeeagent.entity.EmployeeAgent;

import com.veloxa.cockpit.employeeagent.enums.ConversationStatus;
import com.veloxa.cockpit.employeeagent.enums.MemoryStatus;
import com.veloxa.cockpit.employeeagent.enums.MessageRole;

import com.veloxa.cockpit.employeeagent.repository.AgentConversationRepository;
import com.veloxa.cockpit.employeeagent.repository.AgentMemoryRepository;
import com.veloxa.cockpit.employeeagent.repository.AgentMessageRepository;
import com.veloxa.cockpit.employeeagent.repository.EmployeeAgentRepository;

import com.veloxa.cockpit.employeeagent.service.EmployeeAgentConversationService;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.stereotype.Service;
import org.springframework.transaction.PlatformTransactionManager;
import org.springframework.transaction.TransactionDefinition;
import org.springframework.transaction.support.TransactionTemplate;
import org.springframework.web.client.RestClient;
import org.springframework.web.client.RestClientException;
import org.springframework.web.server.ResponseStatusException;

@Service
public class EmployeeAgentConversationServiceImpl
        implements EmployeeAgentConversationService {

    private static final int MAX_MEMORIES = 50;

    private final EmployeeAgentRepository employeeAgentRepository;
    private final AgentConversationRepository conversationRepository;
    private final AgentMessageRepository messageRepository;
    private final AgentMemoryRepository memoryRepository;

    private final RestClient aiServiceClient;
    private final ObjectMapper objectMapper;
    private final TransactionTemplate transactionTemplate;

    public EmployeeAgentConversationServiceImpl(
            EmployeeAgentRepository employeeAgentRepository,
            AgentConversationRepository conversationRepository,
            AgentMessageRepository messageRepository,
            AgentMemoryRepository memoryRepository,
            RestClient.Builder restClientBuilder,
            ObjectMapper objectMapper,
            PlatformTransactionManager transactionManager,
            @Value("${ai-service.url:http://localhost:8000}") String aiServiceUrl
    ) {

        this.employeeAgentRepository = employeeAgentRepository;
        this.conversationRepository = conversationRepository;
        this.messageRepository = messageRepository;
        this.memoryRepository = memoryRepository;

        this.aiServiceClient = restClientBuilder
                .baseUrl(aiServiceUrl)
                .build();

        this.objectMapper = objectMapper;

        this.transactionTemplate =
                new TransactionTemplate(transactionManager);

        this.transactionTemplate.setPropagationBehavior(
                TransactionDefinition.PROPAGATION_REQUIRES_NEW
        );
    }

    // --------------------------------------------------
    // AGENT DISCOVERY
    // --------------------------------------------------

    @Override
    public List<EmployeeAgentResponse> getEnabledAgents() {

        return employeeAgentRepository
                .findAllByEnabledTrueOrderByEmployeeCodeAsc()
                .stream()
                .map(this::toAgentResponse)
                .toList();
    }

    @Override
    public EmployeeAgentResponse getAgent(String employeeCode) {

        return toAgentResponse(findAgent(employeeCode));
    }

    // --------------------------------------------------
    // CONVERSATION MANAGEMENT
    // --------------------------------------------------

    @Override
    public ConversationResponse createConversation(
            String employeeCode,
            CreateConversationRequest request
    ) {

        EmployeeAgent agent = findAgent(employeeCode);

        if (!agent.isEnabled()) {
            throw new ResponseStatusException(
                    HttpStatus.CONFLICT,
                    "This employee agent is currently disabled."
            );
        }

        AgentConversation conversation = AgentConversation.builder()
                .agent(agent)
                .title(normalizeTitle(request.title()))
                .status(ConversationStatus.ACTIVE)
                .build();

        return toConversationResponse(
                conversationRepository.save(conversation)
        );
    }

    @Override
    public List<ConversationResponse> getConversations(
            String employeeCode
    ) {

        findAgent(employeeCode);

        return conversationRepository
                .findAllByAgent_EmployeeCodeOrderByUpdatedAtDesc(employeeCode)
                .stream()
                .map(this::toConversationResponse)
                .toList();
    }

    @Override
    public ConversationResponse getConversation(UUID conversationId) {

        return toConversationResponse(findConversation(conversationId));
    }

    @Override
    public List<AgentMessageResponse> getMessages(UUID conversationId) {

        findConversation(conversationId);

        return messageRepository
                .findAllByConversation_IdOrderByCreatedAtAscIdAsc(
                        conversationId
                )
                .stream()
                .map(this::toMessageResponse)
                .toList();
    }

    // --------------------------------------------------
    // MESSAGE SUBMISSION
    // --------------------------------------------------

    @Override
    public SendAgentMessageResponse sendMessage(
            UUID conversationId,
            SendAgentMessageRequest request
    ) {

        String content = request.content().trim();

        if (content.isBlank()) {
            throw new ResponseStatusException(
                    HttpStatus.BAD_REQUEST,
                    "Message content cannot be empty."
            );
        }

        /*
         * Step 1:
         * Load conversation and agent.
         */
        AgentConversation conversation = findConversation(conversationId);

        if (conversation.getStatus() != ConversationStatus.ACTIVE) {
            throw new ResponseStatusException(
                    HttpStatus.CONFLICT,
                    "This conversation is archived."
            );
        }

        EmployeeAgent agent = conversation.getAgent();

        if (!agent.isEnabled()) {
            throw new ResponseStatusException(
                    HttpStatus.CONFLICT,
                    "This employee agent is currently disabled."
            );
        }

        /*
         * Step 2:
         * Persist the user's message in its own transaction.
         *
         * This transaction commits before the AI service is called.
         * Therefore, an AI failure does not erase the user's message.
         */
        AgentMessage userMessage = transactionTemplate.execute(status -> {

            AgentMessage message = AgentMessage.create(
                    conversation,
                    MessageRole.USER,
                    content,
                    Map.of(),
                    Map.of()
            );

            AgentMessage savedMessage = messageRepository.save(message);

            // Update the conversation's updated_at timestamp.
            conversationRepository.save(conversation);

            return savedMessage;
        });

        if (userMessage == null) {
            throw new ResponseStatusException(
                    HttpStatus.INTERNAL_SERVER_ERROR,
                    "Could not persist the user message."
            );
        }

        /*
         * Step 3:
         * Load active memories and build the employee context.
         */
        Map<String, Object> employeeContext =
                buildEmployeeContext(agent);

        /*
         * Step 4:
         * Prepare the request expected by FastAPI.
         */
        Map<String, Object> aiRequest = new HashMap<>();

        aiRequest.put("question", content);
        aiRequest.put("employee_context", employeeContext);

        /*
         * Step 5:
         * Call the existing employee-agent AI endpoint.
         */
        Map<String, Object> aiResponse = callAiService(aiRequest);

        /*
         * Step 6:
         * Extract the answer and supporting information.
         */
        String answer = readRequiredString(aiResponse, "answer");

        List<String> retrievalSources =
                readStringList(aiResponse.get("retrieval_sources"));

        List<Map<String, Object>> evidence =
                readMapList(aiResponse.get("evidence"));

        Map<String, Object> confidence =
                readMap(aiResponse.get("confidence"));

        List<String> limitations =
                readStringList(aiResponse.get("limitations"));

        /*
         * Step 7:
         * Save the assistant response in a separate transaction.
         */
        Map<String, Object> citations = new HashMap<>();
        citations.put("evidence", evidence);

        Map<String, Object> metadata = new HashMap<>();
        metadata.put("retrievalSources", retrievalSources);
        metadata.put("confidence", confidence);
        metadata.put("limitations", limitations);

        AgentMessage assistantMessage =
                transactionTemplate.execute(status -> {

                    AgentMessage message = AgentMessage.create(
                            conversation,
                            MessageRole.ASSISTANT,
                            answer,
                            citations,
                            metadata
                    );

                    AgentMessage savedMessage =
                            messageRepository.save(message);

                    conversationRepository.save(conversation);

                    return savedMessage;
                });

        if (assistantMessage == null) {
            throw new ResponseStatusException(
                    HttpStatus.INTERNAL_SERVER_ERROR,
                    "The AI response was generated but could not be persisted."
            );
        }

        /*
         * Step 8:
         * Return the complete interaction.
         */
        return new SendAgentMessageResponse(
                conversationId,
                toMessageResponse(userMessage),
                toMessageResponse(assistantMessage),
                retrievalSources,
                evidence,
                confidence,
                limitations
        );
    }

    // --------------------------------------------------
    // EMPLOYEE CONTEXT CONSTRUCTION
    // --------------------------------------------------

    private Map<String, Object> buildEmployeeContext(
            EmployeeAgent agent
    ) {

        JsonNode extractedData =
                agent.getSourceRecord().getExtractedData();

        JsonNode employeeData = extractedData.path("data");

        String fullName = readJsonText(employeeData, "Full Name");
        String title = readJsonText(employeeData, "Title");
        String department = readJsonText(employeeData, "Department");

        if (fullName == null || title == null || department == null) {
            throw new ResponseStatusException(
                    HttpStatus.INTERNAL_SERVER_ERROR,
                    "The employee's source record is missing required identity fields."
            );
        }

        List<AgentMemory> activeMemories =
                memoryRepository
                        .findAllByAgent_IdAndMemoryStatusOrderByCreatedAtDesc(
                                agent.getId(),
                                MemoryStatus.ACTIVE
                        );

        List<Map<String, Object>> memoryContexts =
                activeMemories.stream()
                        .limit(MAX_MEMORIES)
                        .map(this::toMemoryContext)
                        .toList();

        Map<String, Object> context = new HashMap<>();

        context.put("employee_code", agent.getEmployeeCode());
        context.put("full_name", fullName);
        context.put("title", title);
        context.put("department", department);
        context.put(
                "persona_config",
                agent.getPersonaConfig() == null
                        ? Map.of()
                        : agent.getPersonaConfig()
        );
        context.put("system_context", agent.getSystemContext());
        context.put("memories", memoryContexts);

        return context;
    }

    private Map<String, Object> toMemoryContext(AgentMemory memory) {

        Map<String, Object> context = new HashMap<>();

        context.put("memory_type", memory.getMemoryType().name());
        context.put("content", memory.getContent());

        context.put(
                "source_references",
                memory.getSourceReferences() == null
                        ? Map.of()
                        : memory.getSourceReferences()
        );

        BigDecimal confidence = memory.getConfidence();

        context.put(
                "confidence",
                confidence == null ? null : confidence.doubleValue()
        );

        return context;
    }

    // --------------------------------------------------
    // AI SERVICE COMMUNICATION
    // --------------------------------------------------

    private Map<String, Object> callAiService(
            Map<String, Object> request
    ) {

        try {

            Map<String, Object> response = aiServiceClient.post()
                    .uri("/api/v1/employee-agents/respond")
                    .contentType(MediaType.APPLICATION_JSON)
                    .accept(MediaType.APPLICATION_JSON)
                    .body(request)
                    .retrieve()
                    .body(
                            new org.springframework.core.ParameterizedTypeReference<>() {}
                    );

            if (response == null) {
                throw new ResponseStatusException(
                        HttpStatus.BAD_GATEWAY,
                        "The AI service returned an empty response."
                );
            }

            return response;

        } catch (RestClientException exception) {

            throw new ResponseStatusException(
                    HttpStatus.BAD_GATEWAY,
                    "The employee agent could not be reached or failed to respond. "
                            + "The user's message has been saved.",
                    exception
            );
        }
    }

    // --------------------------------------------------
    // ENTITY LOOKUPS
    // --------------------------------------------------

    private EmployeeAgent findAgent(String employeeCode) {

        return employeeAgentRepository
                .findByEmployeeCode(employeeCode)
                .orElseThrow(() -> new ResponseStatusException(
                        HttpStatus.NOT_FOUND,
                        "Employee agent not found: " + employeeCode
                ));
    }

    private AgentConversation findConversation(UUID conversationId) {

        return conversationRepository
                .findById(conversationId)
                .orElseThrow(() -> new ResponseStatusException(
                        HttpStatus.NOT_FOUND,
                        "Conversation not found: " + conversationId
                ));
    }

    // --------------------------------------------------
    // RESPONSE MAPPERS
    // --------------------------------------------------

    private EmployeeAgentResponse toAgentResponse(EmployeeAgent agent) {

        JsonNode data = agent.getSourceRecord()
                .getExtractedData()
                .path("data");

        return new EmployeeAgentResponse(
                agent.getId(),
                agent.getEmployeeCode(),
                agent.getAgentKey(),
                readJsonText(data, "Full Name"),
                readJsonText(data, "Title"),
                readJsonText(data, "Department"),
                readJsonText(data, "Status"),
                agent.isEnabled()
        );
    }

    private ConversationResponse toConversationResponse(
            AgentConversation conversation
    ) {

        EmployeeAgent agent = conversation.getAgent();

        JsonNode data = agent.getSourceRecord()
                .getExtractedData()
                .path("data");

        return new ConversationResponse(
                conversation.getId(),
                agent.getEmployeeCode(),
                readJsonText(data, "Full Name"),
                agent.getAgentKey(),
                conversation.getTitle(),
                conversation.getStatus(),
                conversation.getCreatedAt(),
                conversation.getUpdatedAt()
        );
    }

    private AgentMessageResponse toMessageResponse(AgentMessage message) {

        return new AgentMessageResponse(
                message.getId(),
                message.getRole(),
                message.getContent(),
                message.getCitations(),
                message.getMetadata(),
                message.getCreatedAt()
        );
    }

    // --------------------------------------------------
    // SAFE DATA CONVERSION
    // --------------------------------------------------

    private String readJsonText(JsonNode node, String fieldName) {

        JsonNode value = node.path(fieldName);

        if (value.isMissingNode() || value.isNull()) {
            return null;
        }

        String text = value.asText();

        return text == null || text.isBlank() ? null : text;
    }

    private String readRequiredString(
            Map<String, Object> response,
            String field
    ) {

        Object value = response.get(field);

        if (!(value instanceof String text) || text.isBlank()) {
            throw new ResponseStatusException(
                    HttpStatus.BAD_GATEWAY,
                    "The AI service returned an invalid response: missing "
                            + field
            );
        }

        return text;
    }

    private List<String> readStringList(Object value) {

        if (!(value instanceof List<?> list)) {
            return List.of();
        }

        return list.stream()
                .filter(String.class::isInstance)
                .map(String.class::cast)
                .toList();
    }

    private List<Map<String, Object>> readMapList(Object value) {

        if (!(value instanceof List<?> list)) {
            return List.of();
        }

        List<Map<String, Object>> result = new ArrayList<>();

        for (Object item : list) {

            if (item instanceof Map<?, ?> map) {

                Map<String, Object> converted = new HashMap<>();

                map.forEach((key, mapValue) -> {
                    if (key instanceof String stringKey) {
                        converted.put(stringKey, mapValue);
                    }
                });

                result.add(converted);
            }
        }

        return result;
    }

    private Map<String, Object> readMap(Object value) {

        if (!(value instanceof Map<?, ?> map)) {
            return Map.of();
        }

        Map<String, Object> result = new HashMap<>();

        map.forEach((key, mapValue) -> {
            if (key instanceof String stringKey) {
                result.put(stringKey, mapValue);
            }
        });

        return result;
    }

    private String normalizeTitle(String title) {

        if (title == null || title.isBlank()) {
            return null;
        }

        return title.trim();
    }
}
