
package com.veloxa.cockpit.employeeagent.controller;

import com.veloxa.cockpit.employeeagent.dto.AgentMemoryResponse;
import com.veloxa.cockpit.employeeagent.dto.CreateAgentMemoryRequest;
import com.veloxa.cockpit.employeeagent.service.AgentMemoryService;

import jakarta.validation.Valid;

import lombok.RequiredArgsConstructor;

import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.UUID;

@RestController
@RequestMapping("/api/v1/employee-agents/{employeeCode}/memories")
@RequiredArgsConstructor
public class AgentMemoryController {

    private final AgentMemoryService agentMemoryService;

    @GetMapping
    public List<AgentMemoryResponse> getMemories(@PathVariable String employeeCode) {
        return agentMemoryService.getMemories(employeeCode);
    }

    @PostMapping
    @ResponseStatus(HttpStatus.CREATED)
    public AgentMemoryResponse createMemory(@PathVariable String employeeCode, @Valid @RequestBody CreateAgentMemoryRequest request) {
        return agentMemoryService.createMemory(employeeCode, request);
    }

    @PatchMapping("/{memoryId}/retract")
    public AgentMemoryResponse retractMemory(@PathVariable String employeeCode, @PathVariable UUID memoryId) {
        return agentMemoryService.retractMemory(employeeCode, memoryId);
    }
}
