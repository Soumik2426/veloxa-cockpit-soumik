
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
import org.hibernate.annotations.UuidGenerator;
import org.hibernate.type.SqlTypes;

import lombok.AccessLevel;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

@Entity
@Table(name = "agent_memories")
@Getter
@Setter
@Builder
@NoArgsConstructor(access = AccessLevel.PROTECTED)
@AllArgsConstructor(access = AccessLevel.PACKAGE)
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

    @Builder.Default
    @JdbcTypeCode(SqlTypes.JSON)
    @Column(name = "source_references", nullable = false, columnDefinition = "jsonb")
    private Map<String, Object> sourceReferences = new HashMap<>();

    @Column(name = "confidence", precision = 5, scale = 4)
    private BigDecimal confidence;

    @Builder.Default
    @Enumerated(EnumType.STRING)
    @Column(name = "memory_status", nullable = false, length = 20)
    private MemoryStatus memoryStatus = MemoryStatus.ACTIVE;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "supersedes_memory_id")
    private AgentMemory supersedesMemory;

    @Builder.Default
    @Column(name = "valid_from", nullable = false)
    private OffsetDateTime validFrom = OffsetDateTime.now();

    @Column(name = "valid_until")
    private OffsetDateTime validUntil;

    @CreationTimestamp
    @Column(name = "created_at", nullable = false, updatable = false)
    private OffsetDateTime createdAt;
}
