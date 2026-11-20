package com.veloxa.cockpit.employeeagent.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;

import java.time.LocalDate;

public record SendAgentMessageRequest(

        @NotBlank(message = "Message content cannot be empty")
        @Size(max = 2000, message = "Message cannot exceed 2000 characters")
        String content,

        LocalDate asOfDate
) {}
