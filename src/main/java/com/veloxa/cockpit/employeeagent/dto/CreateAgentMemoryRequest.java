package com.veloxa.cockpit.employeeagent.dto;

import com.veloxa.cockpit.employeeagent.enums.MemoryType;
import jakarta.validation.constraints.DecimalMax;
import jakarta.validation.constraints.DecimalMin;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;

import java.math.BigDecimal;
import java.time.OffsetDateTime;
import java.util.Map;
import java.util.UUID;

public record CreateAgentMemoryRequest(

        @NotNull
        MemoryType memoryType,

        @NotBlank
        @Size(max = 4000)
        String content,

        Map<String, Object> sourceReferences,

        @DecimalMin("0.0")
        @DecimalMax("1.0")
        BigDecimal confidence,

        OffsetDateTime validFrom,

        UUID supersedesMemoryId
) {}
