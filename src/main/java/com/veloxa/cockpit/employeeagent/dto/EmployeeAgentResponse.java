package com.veloxa.cockpit.employeeagent.dto;

import java.util.UUID;

public record EmployeeAgentResponse(
        UUID id,
        String employeeCode,
        String agentKey,
        String fullName,
        String designation,
        String department,
        String employmentStatus,
        boolean enabled
) {
}
