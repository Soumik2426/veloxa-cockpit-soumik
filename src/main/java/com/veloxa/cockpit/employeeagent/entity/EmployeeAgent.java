
package com.veloxa.cockpit.employeeagent.entity;

import java.time.OffsetDateTime;
import java.util.HashMap;
import java.util.Map;
import java.util.UUID;

import jakarta.persistence.*;

import org.hibernate.annotations.CreationTimestamp;
import org.hibernate.annotations.JdbcTypeCode;
import org.hibernate.annotations.UpdateTimestamp;
import org.hibernate.type.SqlTypes;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

@Entity
@Table(
        name = "employee_agents",
        uniqueConstraints = {
                @UniqueConstraint(
                        name = "uk_employee_agents_source_record",
                        columnNames = "source_record_id"
                ),
                @UniqueConstraint(
                        name = "uk_employee_agents_employee_code",
                        columnNames = "employee_code"
                ),
                @UniqueConstraint(
                        name = "uk_employee_agents_agent_key",
                        columnNames = "agent_key"
                )
        },
        indexes = {
                @Index(
                        name = "idx_employee_agents_enabled",
                        columnList = "enabled"
                )
        }
)
@Getter
@Setter
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class EmployeeAgent {

    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    @Column(name = "id", nullable = false, updatable = false)
    private UUID id;

    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(
            name = "source_record_id",
            nullable = false,
            updatable = false
    )
    private ExtractedRecord sourceRecord;

    @Column(name = "employee_code", nullable = false, length = 20)
    private String employeeCode;

    @Column(name = "agent_key", nullable = false, length = 50)
    private String agentKey;

    @Builder.Default
    @JdbcTypeCode(SqlTypes.JSON)
    @Column(name = "persona_config", nullable = false, columnDefinition = "jsonb")
    private Map<String, Object> personaConfig = new HashMap<>();

    @Column(name = "system_context", columnDefinition = "TEXT")
    private String systemContext;

    @Builder.Default
    @Column(name = "enabled", nullable = false)
    private boolean enabled = true;

    @CreationTimestamp
    @Column(name = "created_at", nullable = false, updatable = false)
    private OffsetDateTime createdAt;

    @UpdateTimestamp
    @Column(name = "updated_at", nullable = false)
    private OffsetDateTime updatedAt;
}
