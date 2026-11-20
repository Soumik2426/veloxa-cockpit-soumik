package com.veloxa.cockpit.risk.entity;

import java.time.LocalDate;
import java.time.OffsetDateTime;
import java.util.UUID;

import com.fasterxml.jackson.databind.JsonNode;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.Table;
import jakarta.persistence.UniqueConstraint;

import org.hibernate.annotations.JdbcTypeCode;
import org.hibernate.type.SqlTypes;

import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

@Entity
@Table(
        name = "risk_assessment_snapshot",
        uniqueConstraints = @UniqueConstraint(
                name = "uk_risk_assessment_date",
                columnNames = "assessment_date"
        )
)
@Getter
@Setter
@NoArgsConstructor
public class RiskAssessmentSnapshot {

    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    private UUID id;

    @Column(name = "assessment_date", nullable = false)
    private LocalDate assessmentDate;

    @Column(name = "generated_at")
    private OffsetDateTime generatedAt;

    @Column(name = "updated_at", nullable = false)
    private OffsetDateTime updatedAt;

    @Column(nullable = false, length = 20)
    private String status;

    @JdbcTypeCode(SqlTypes.JSON)
    @Column(columnDefinition = "jsonb")
    private JsonNode assessment;

    @Column(name = "data_version", length = 200)
    private String dataVersion;

    @Column(name = "error_message", columnDefinition = "TEXT")
    private String errorMessage;
}
