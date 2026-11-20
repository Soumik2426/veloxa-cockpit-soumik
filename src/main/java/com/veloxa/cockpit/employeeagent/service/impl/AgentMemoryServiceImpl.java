package com.veloxa.cockpit.employeeagent.service.impl;

import com.veloxa.cockpit.employeeagent.dto.AgentMemoryResponse;
import com.veloxa.cockpit.employeeagent.dto.CreateAgentMemoryRequest;
import com.veloxa.cockpit.employeeagent.entity.AgentMemory;
import com.veloxa.cockpit.employeeagent.entity.EmployeeAgent;
import com.veloxa.cockpit.employeeagent.enums.MemoryStatus;
import com.veloxa.cockpit.employeeagent.repository.AgentMemoryRepository;
import com.veloxa.cockpit.employeeagent.repository.EmployeeAgentRepository;
import com.veloxa.cockpit.employeeagent.service.AgentMemoryService;

import lombok.RequiredArgsConstructor;

import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.server.ResponseStatusException;

import java.time.OffsetDateTime;
import java.util.List;
import java.util.Map;
import java.util.UUID;

@Service
@RequiredArgsConstructor
@Transactional(readOnly = true)
public class AgentMemoryServiceImpl implements AgentMemoryService {

    private final EmployeeAgentRepository employeeAgentRepository;
    private final AgentMemoryRepository agentMemoryRepository;

    @Override
    public List<AgentMemoryResponse> getMemories(String employeeCode) {

        employeeAgentRepository.findByEmployeeCode(employeeCode)
                .orElseThrow(() -> new ResponseStatusException(
                        HttpStatus.NOT_FOUND,
                        "Employee agent not found: " + employeeCode
                ));

        return agentMemoryRepository
                .findAllByAgent_EmployeeCodeOrderByCreatedAtDesc(employeeCode)
                .stream()
                .map(this::toResponse)
                .toList();
    }

    @Override
    @Transactional
    public AgentMemoryResponse createMemory(
            String employeeCode,
            CreateAgentMemoryRequest request
    ) {

        EmployeeAgent agent = employeeAgentRepository
                .findByEmployeeCode(employeeCode)
                .orElseThrow(() -> new ResponseStatusException(
                        HttpStatus.NOT_FOUND,
                        "Employee agent not found: " + employeeCode
                ));

        OffsetDateTime effectiveFrom = request.validFrom() != null
                ? request.validFrom()
                : OffsetDateTime.now();

        AgentMemory previousMemory = null;

        if (request.supersedesMemoryId() != null) {

            previousMemory = agentMemoryRepository
                    .findByIdAndAgent_Id(
                            request.supersedesMemoryId(),
                            agent.getId()
                    )
                    .orElseThrow(() -> new ResponseStatusException(
                            HttpStatus.NOT_FOUND,
                            "Memory to supersede was not found for this employee agent"
                    ));

            if (previousMemory.getMemoryStatus() != MemoryStatus.ACTIVE) {
                throw new ResponseStatusException(
                        HttpStatus.CONFLICT,
                        "Only an active memory can be superseded"
                );
            }

            try {
                previousMemory.supersede(effectiveFrom);
            } catch (IllegalArgumentException | IllegalStateException exception) {
                throw new ResponseStatusException(
                        HttpStatus.BAD_REQUEST,
                        exception.getMessage()
                );
            }

            agentMemoryRepository.save(previousMemory);
        }

        Map<String, Object> sourceReferences =
                request.sourceReferences() == null
                        ? Map.of()
                        : request.sourceReferences();

        AgentMemory newMemory = AgentMemory.create(
                agent,
                request.memoryType(),
                request.content().trim(),
                sourceReferences,
                request.confidence(),
                effectiveFrom,
                previousMemory
        );

        AgentMemory savedMemory = agentMemoryRepository.save(newMemory);

        return toResponse(savedMemory);
    }

    @Override
    @Transactional
    public AgentMemoryResponse retractMemory(
            String employeeCode,
            UUID memoryId
    ) {

        EmployeeAgent agent = employeeAgentRepository
                .findByEmployeeCode(employeeCode)
                .orElseThrow(() -> new ResponseStatusException(
                        HttpStatus.NOT_FOUND,
                        "Employee agent not found: " + employeeCode
                ));

        AgentMemory memory = agentMemoryRepository
                .findByIdAndAgent_Id(memoryId, agent.getId())
                .orElseThrow(() -> new ResponseStatusException(
                        HttpStatus.NOT_FOUND,
                        "Memory not found for this employee agent"
                ));

        if (memory.getMemoryStatus() != MemoryStatus.ACTIVE) {
            throw new ResponseStatusException(
                    HttpStatus.CONFLICT,
                    "Only an active memory can be retracted"
            );
        }

        memory.retract();

        return toResponse(agentMemoryRepository.save(memory));
    }

    private AgentMemoryResponse toResponse(AgentMemory memory) {

        return new AgentMemoryResponse(
                memory.getId(),
                memory.getAgent().getEmployeeCode(),
                memory.getMemoryType(),
                memory.getContent(),
                memory.getSourceReferences(),
                memory.getConfidence(),
                memory.getMemoryStatus(),
                memory.getSupersedesMemory() != null
                        ? memory.getSupersedesMemory().getId()
                        : null,
                memory.getValidFrom(),
                memory.getValidUntil(),
                memory.getCreatedAt()
        );
    }
}
