package com.veloxa.cockpit.employeeagent.dto;

import java.util.List;

public record EmployeeAgentRegistrationResponse(
        int expectedCount,
        int foundCount,
        int createdCount,
        int alreadyRegisteredCount,
        List<EmployeeAgentRegistrationItem> agents
) {
}