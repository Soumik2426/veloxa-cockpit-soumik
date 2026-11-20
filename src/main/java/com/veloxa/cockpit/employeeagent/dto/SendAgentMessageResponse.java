
package com.veloxa.cockpit.employeeagent.dto;

import java.util.List;
import java.util.Map;
import java.util.UUID;

public record SendAgentMessageResponse(
        UUID conversationId,
        AgentMessageResponse userMessage,
        AgentMessageResponse assistantMessage,
        List<String> retrievalSources,
        List<Map<String, Object>> evidence,
        Map<String, Object> confidence,
        List<String> limitations
) {}
