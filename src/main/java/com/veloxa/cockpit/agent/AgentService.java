package com.veloxa.cockpit.agent;

import java.util.Map;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.core.ParameterizedTypeReference;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestClient;
import org.springframework.web.client.RestClientException;
import org.springframework.web.server.ResponseStatusException;

@Service
public class AgentService {

    private static final ParameterizedTypeReference<Map<String, Object>> RESPONSE_TYPE =
            new ParameterizedTypeReference<>() {};

    private final RestClient aiServiceClient;
    private final ObjectMapper objectMapper;

    public AgentService(
            RestClient.Builder restClientBuilder,
            ObjectMapper objectMapper,
            @Value("${ai-service.url:http://localhost:8000}") String aiServiceUrl) {

        this.aiServiceClient = restClientBuilder
                .baseUrl(aiServiceUrl)
                .build();

        this.objectMapper = objectMapper;
    }

    public Map<String, Object> ask(AgentController.AskRequest request) {

        try {
            System.out.println("========================================");
            System.out.println("Spring Boot received agent request");
            System.out.println("Question: " + request.question());

            Map<String, String> requestBody = Map.of(
                    "question", request.question()
            );

            String jsonBody = objectMapper.writeValueAsString(requestBody);

            System.out.println("Serialized JSON request: " + jsonBody);
            System.out.println("Forwarding request to: http://localhost:8000/api/v1/agent/ask");
            System.out.println("========================================");

            Map<String, Object> response = aiServiceClient.post()
                    .uri("/api/v1/agent/ask")
                    .contentType(MediaType.APPLICATION_JSON)
                    .accept(MediaType.APPLICATION_JSON)
                    .body(jsonBody)
                    .retrieve()
                    .body(RESPONSE_TYPE);

            System.out.println("========================================");
            System.out.println("AI service response received successfully");
            System.out.println("Response: " + response);
            System.out.println("========================================");

            return response;

        } catch (JsonProcessingException exception) {

            System.err.println("Failed to serialize agent request:");
            exception.printStackTrace();

            throw new ResponseStatusException(
                    HttpStatus.INTERNAL_SERVER_ERROR,
                    "Could not serialize the agent request.",
                    exception);

        } catch (RestClientException exception) {

            System.err.println("========================================");
            System.err.println("AI SERVICE REQUEST FAILED");
            System.err.println("Error: " + exception.getMessage());
            exception.printStackTrace();
            System.err.println("========================================");

            throw new ResponseStatusException(
                    HttpStatus.BAD_GATEWAY,
                    "The AI service could not complete the request.",
                    exception);
        }
    }
}
