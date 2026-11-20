package com.veloxa.cockpit.employeeagent.dto;

import java.time.OffsetDateTime;
import java.util.Map;
import java.util.UUID;

import com.veloxa.cockpit.employeeagent.enums.MessageRole;

public record AgentMessageResponse(
        UUID id,
        MessageRole role,
        String content,
        Map<String, Object> citations,
        Map<String, Object> metadata,
        OffsetDateTime createdAt
) {
}
