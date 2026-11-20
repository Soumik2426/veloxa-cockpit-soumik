
package com.veloxa.cockpit.employeeagent.repository;

import java.util.List;
import java.util.Optional;
import java.util.UUID;

import com.veloxa.cockpit.employeeagent.entity.AgentMemory;
import com.veloxa.cockpit.employeeagent.enums.MemoryStatus;

import org.springframework.data.jpa.repository.JpaRepository;

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
}
