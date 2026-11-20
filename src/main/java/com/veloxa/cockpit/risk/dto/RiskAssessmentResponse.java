package com.veloxa.cockpit.risk.dto;

import java.time.LocalDate;
import java.time.OffsetDateTime;
import java.util.UUID;

import com.fasterxml.jackson.databind.JsonNode;

public record RiskAssessmentResponse(
        UUID id,
        LocalDate assessmentDate,
        OffsetDateTime generatedAt,
        OffsetDateTime updatedAt,
        String status,
        JsonNode assessment,
        String dataVersion,
        String errorMessage
) {
}
