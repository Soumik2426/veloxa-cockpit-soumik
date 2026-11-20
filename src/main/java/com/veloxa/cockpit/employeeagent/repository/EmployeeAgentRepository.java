package com.veloxa.cockpit.employeeagent.repository;

import java.util.Collection;
import java.util.List;
import java.util.Optional;
import java.util.UUID;

import com.veloxa.cockpit.employeeagent.entity.EmployeeAgent;

import org.springframework.data.jpa.repository.JpaRepository;

public interface EmployeeAgentRepository
        extends JpaRepository<EmployeeAgent, UUID> {

    Optional<EmployeeAgent> findByEmployeeCode(String employeeCode);

    Optional<EmployeeAgent> findByAgentKey(String agentKey);

    List<EmployeeAgent> findAllByEmployeeCodeIn(
            Collection<String> employeeCodes
    );

    List<EmployeeAgent> findAllByEnabledTrueOrderByEmployeeCodeAsc();

    boolean existsByEmployeeCode(String employeeCode);

    boolean existsByAgentKey(String agentKey);
}