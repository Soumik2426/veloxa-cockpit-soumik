package com.veloxa.cockpit.employeeagent.entity;

import java.math.BigDecimal;
import java.time.OffsetDateTime;
import java.util.HashMap;
import java.util.Map;
import java.util.UUID;

import com.veloxa.cockpit.employeeagent.enums.MemoryStatus;
import com.veloxa.cockpit.employeeagent.enums.MemoryType;

import jakarta.persistence.*;
import org.hibernate.annotations.CreationTimestamp;
import org.hibernate.annotations.JdbcTypeCode;
import org.hibernate.type.SqlTypes;

import lombok.AccessLevel;
import lombok.Getter;
import lombok.NoArgsConstructor;

@Entity
@Table(name = "agent_memories")
@Getter
@NoArgsConstructor(access = AccessLevel.PROTECTED)
public class AgentMemory {

    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    private UUID id;

    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "agent_id", nullable = false, updatable = false)
    private EmployeeAgent agent;

    @Enumerated(EnumType.STRING)
    @Column(name = "memory_type", nullable = false, length = 30)
    private MemoryType memoryType;

    @Column(name = "content", nullable = false, columnDefinition = "TEXT")
    private String content;

    @JdbcTypeCode(SqlTypes.JSON)
    @Column(name = "source_references", nullable = false, columnDefinition = "jsonb")
    private Map<String, Object> sourceReferences = new HashMap<>();

    @Column(name = "confidence", precision = 5, scale = 4)
    private BigDecimal confidence;

    @Enumerated(EnumType.STRING)
    @Column(name = "memory_status", nullable = false, length = 20)
    private MemoryStatus memoryStatus = MemoryStatus.ACTIVE;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "supersedes_memory_id")
    private AgentMemory supersedesMemory;

    @Column(name = "valid_from", nullable = false)
    private OffsetDateTime validFrom = OffsetDateTime.now();

    @Column(name = "valid_until")
    private OffsetDateTime validUntil;

    @CreationTimestamp
    @Column(name = "created_at", nullable = false, updatable = false)
    private OffsetDateTime createdAt;

    private AgentMemory(
            EmployeeAgent agent,
            MemoryType memoryType,
            String content,
            Map<String, Object> sourceReferences,
            BigDecimal confidence,
            OffsetDateTime validFrom,
            AgentMemory supersedesMemory
    ) {
        this.agent = agent;
        this.memoryType = memoryType;
        this.content = content;
        this.sourceReferences = sourceReferences == null
                ? new HashMap<>()
                : new HashMap<>(sourceReferences);
        this.confidence = confidence;
        this.validFrom = validFrom == null
                ? OffsetDateTime.now()
                : validFrom;
        this.supersedesMemory = supersedesMemory;
    }

    public static AgentMemory create(
            EmployeeAgent agent,
            MemoryType memoryType,
            String content,
            Map<String, Object> sourceReferences,
            BigDecimal confidence,
            OffsetDateTime validFrom,
            AgentMemory supersedesMemory
    ) {
        return new AgentMemory(
                agent,
                memoryType,
                content,
                sourceReferences,
                confidence,
                validFrom,
                supersedesMemory
        );
    }

    public void supersede(OffsetDateTime effectiveAt) {

        if (memoryStatus != MemoryStatus.ACTIVE) {
            throw new IllegalStateException(
                    "Only active memories can be superseded."
            );
        }

        if (effectiveAt == null || effectiveAt.isBefore(validFrom)) {
            throw new IllegalArgumentException(
                    "The supersession date cannot precede the memory's valid-from date."
            );
        }

        this.memoryStatus = MemoryStatus.SUPERSEDED;
        this.validUntil = effectiveAt;
    }

    public void retract() {

        if (memoryStatus != MemoryStatus.ACTIVE) {
            throw new IllegalStateException(
                    "Only active memories can be retracted."
            );
        }

        this.memoryStatus = MemoryStatus.RETRACTED;
        this.validUntil = OffsetDateTime.now();
    }
}
