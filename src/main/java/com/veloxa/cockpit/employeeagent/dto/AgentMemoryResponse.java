package com.veloxa.cockpit.employeeagent.dto;

import com.veloxa.cockpit.employeeagent.enums.MemoryStatus;
import com.veloxa.cockpit.employeeagent.enums.MemoryType;

import java.math.BigDecimal;
import java.time.OffsetDateTime;
import java.util.Map;
import java.util.UUID;

public record AgentMemoryResponse(
        UUID id,
        String employeeCode,
        MemoryType memoryType,
        String content,
        Map<String, Object> sourceReferences,
        BigDecimal confidence,
        MemoryStatus memoryStatus,
        UUID supersedesMemoryId,
        OffsetDateTime validFrom,
        OffsetDateTime validUntil,
        OffsetDateTime createdAt
) {}
