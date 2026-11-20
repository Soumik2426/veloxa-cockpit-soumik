package com.veloxa.cockpit.employeeagent.service;

import java.util.List;
import java.util.UUID;

import com.veloxa.cockpit.employeeagent.dto.*;

public interface EmployeeAgentConversationService {

    List<EmployeeAgentResponse> getEnabledAgents();
    EmployeeAgentResponse getAgent(String employeeCode);
    ConversationResponse createConversation(
            String employeeCode,
            CreateConversationRequest request
    );
    List<ConversationResponse> getConversations(String employeeCode);

    ConversationResponse getConversation(UUID conversationId);

    List<AgentMessageResponse> getMessages(UUID conversationId);

    SendAgentMessageResponse sendMessage(
            UUID conversationId,
            SendAgentMessageRequest request
    );
}
