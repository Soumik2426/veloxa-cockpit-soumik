package com.veloxa.cockpit.employeeagent.entity;

import java.time.OffsetDateTime;
import java.util.UUID;

import com.fasterxml.jackson.databind.JsonNode;

import org.hibernate.annotations.Immutable;
import org.hibernate.annotations.JdbcTypeCode;
import org.hibernate.type.SqlTypes;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.Table;

import lombok.AccessLevel;
import lombok.Getter;
import lombok.NoArgsConstructor;

@Entity
@Immutable
@Table(name = "extracted_record")
@Getter
@NoArgsConstructor(access = AccessLevel.PROTECTED)
public class ExtractedRecord {

    @Id
    @Column(name = "id", nullable = false)
    private UUID id;

    @Column(name = "ingestion_file_id", nullable = false)
    private UUID ingestionFileId;

    @Column(name = "record_type", nullable = false, length = 100)
    private String recordType;

    @Column(name = "record_key", length = 255)
    private String recordKey;

    @JdbcTypeCode(SqlTypes.JSON)
    @Column(name = "source_locator", nullable = false, columnDefinition = "jsonb")
    private JsonNode sourceLocator;

    @JdbcTypeCode(SqlTypes.JSON)
    @Column(name = "extracted_data", nullable = false, columnDefinition = "jsonb")
    private JsonNode extractedData;

    @Column(name = "extraction_method", nullable = false, length = 50)
    private String extractionMethod;

    @Column(name = "extraction_status", nullable = false, length = 30)
    private String extractionStatus;

    @Column(name = "confidence_score")
    private Double confidenceScore;

    @Column(name = "created_at", nullable = false)
    private OffsetDateTime createdAt;
}
