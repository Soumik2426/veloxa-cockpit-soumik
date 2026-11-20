
package com.veloxa.cockpit.employeeagent.service;

import com.veloxa.cockpit.employeeagent.dto.AgentMemoryResponse;
import com.veloxa.cockpit.employeeagent.dto.CreateAgentMemoryRequest;

import java.util.List;
import java.util.UUID;

public interface AgentMemoryService {

    List<AgentMemoryResponse> getMemories(String employeeCode);

    AgentMemoryResponse createMemory(
            String employeeCode,
            CreateAgentMemoryRequest request
    );

    AgentMemoryResponse retractMemory(
            String employeeCode,
            UUID memoryId
    );
}
