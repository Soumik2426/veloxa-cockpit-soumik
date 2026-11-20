package com.veloxa.cockpit.employeeagent.dto;

import jakarta.validation.constraints.Size;

public record CreateConversationRequest(
        @Size(max = 200, message = "Conversation title cannot exceed 200 characters")
        String title
) {
}
