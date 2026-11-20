
package com.veloxa.cockpit.employeeagent.repository;

import java.time.OffsetDateTime;
import java.util.List;
import java.util.Optional;
import java.util.UUID;

import com.veloxa.cockpit.employeeagent.entity.AgentMemory;
import com.veloxa.cockpit.employeeagent.enums.MemoryStatus;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

public interface AgentMemoryRepository
        extends JpaRepository<AgentMemory, UUID> {

    List<AgentMemory> findAllByAgent_IdAndMemoryStatusOrderByCreatedAtDesc(
            UUID agentId,
            MemoryStatus memoryStatus
    );

    List<AgentMemory> findAllByAgent_EmployeeCodeAndMemoryStatusOrderByCreatedAtDesc(
            String employeeCode,
            MemoryStatus memoryStatus
    );

    Optional<AgentMemory> findByIdAndAgent_Id(
            UUID memoryId,
            UUID agentId
    );

    List<AgentMemory> findAllBySupersedesMemory_Id(
            UUID supersededMemoryId
    );

    long countByAgent_IdAndMemoryStatus(
            UUID agentId,
            MemoryStatus memoryStatus
    );

    @Query("""
    SELECT m
    FROM AgentMemory m
    WHERE m.agent.employeeCode = :employeeCode
      AND m.createdAt <= :asOf
      AND (m.validFrom IS NULL OR m.validFrom <= :asOf)
      AND (m.validUntil IS NULL OR m.validUntil > :asOf)
      AND m.memoryStatus <> :retractedStatus
    ORDER BY m.createdAt DESC
    """)
    List<AgentMemory> findMemoriesAsOf(
            @Param("employeeCode") String employeeCode,
            @Param("asOf") OffsetDateTime asOf,
            @Param("retractedStatus") MemoryStatus retractedStatus
    );

    List<AgentMemory> findAllByAgent_EmployeeCodeOrderByCreatedAtDesc(
            String employeeCode
    );

}
