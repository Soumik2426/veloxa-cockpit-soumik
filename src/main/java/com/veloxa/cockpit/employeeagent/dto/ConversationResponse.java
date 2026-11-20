package com.veloxa.cockpit.employeeagent.dto;

import java.time.OffsetDateTime;
import java.util.UUID;

import com.veloxa.cockpit.employeeagent.enums.ConversationStatus;

public record ConversationResponse(
        UUID id,
        String employeeCode,
        String employeeName,
        String agentKey,
        String title,
        ConversationStatus status,
        OffsetDateTime createdAt,
        OffsetDateTime updatedAt
) {
}
