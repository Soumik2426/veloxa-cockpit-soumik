package com.veloxa.cockpit.employeeagent.service.impl;

import java.util.ArrayList;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Set;

import com.fasterxml.jackson.databind.JsonNode;

import com.veloxa.cockpit.employeeagent.dto.EmployeeAgentRegistrationItem;
import com.veloxa.cockpit.employeeagent.dto.EmployeeAgentRegistrationResponse;
import com.veloxa.cockpit.employeeagent.entity.EmployeeAgent;
import com.veloxa.cockpit.employeeagent.entity.ExtractedRecord;
import com.veloxa.cockpit.employeeagent.repository.EmployeeAgentRepository;
import com.veloxa.cockpit.employeeagent.repository.ExtractedRecordRepository;
import com.veloxa.cockpit.employeeagent.service.EmployeeAgentRegistrationService;

import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
public class EmployeeAgentRegistrationServiceImpl
        implements EmployeeAgentRegistrationService {

    private static final List<String> REQUIRED_EMPLOYEE_CODES = List.of(
            "VX001", "VX002", "VX003", "VX004",
            "VX005", "VX006", "VX007", "VX008",
            "VX009", "VX010", "VX011", "VX012",
            "VX013", "VX014"
    );

    private final ExtractedRecordRepository extractedRecordRepository;
    private final EmployeeAgentRepository employeeAgentRepository;

    public EmployeeAgentRegistrationServiceImpl(
            ExtractedRecordRepository extractedRecordRepository,
            EmployeeAgentRepository employeeAgentRepository
    ) {
        this.extractedRecordRepository = extractedRecordRepository;
        this.employeeAgentRepository = employeeAgentRepository;
    }

    @Override
    @Transactional
    public EmployeeAgentRegistrationResponse registerAllAgents() {

        // Fetch the 14 employee master records.
        List<ExtractedRecord> sourceRecords =
                extractedRecordRepository.findEmployeeMasterRecordsByEmployeeCodes(
                        REQUIRED_EMPLOYEE_CODES
                );

        if (sourceRecords.size() != REQUIRED_EMPLOYEE_CODES.size()) {
            throw new IllegalStateException(
                    "Expected exactly 14 employee records, but found "
                            + sourceRecords.size()
            );
        }

        // Validate and map source records by employee code.
        Map<String, ExtractedRecord> recordsByEmployeeCode =
                new LinkedHashMap<>();

        for (ExtractedRecord sourceRecord : sourceRecords) {

            JsonNode data = sourceRecord.getExtractedData().path("data");

            String employeeCode = readText(data, "Emp ID");

            validateEmployeeRecord(sourceRecord, data, employeeCode);

            if (!REQUIRED_EMPLOYEE_CODES.contains(employeeCode)) {
                throw new IllegalStateException(
                        "Unexpected employee code: " + employeeCode
                );
            }

            if (recordsByEmployeeCode.putIfAbsent(
                    employeeCode, sourceRecord
            ) != null) {
                throw new IllegalStateException(
                        "Duplicate employee record found for " + employeeCode
                );
            }
        }

        Set<String> missingCodes = new HashSet<>(REQUIRED_EMPLOYEE_CODES);
        missingCodes.removeAll(recordsByEmployeeCode.keySet());

        if (!missingCodes.isEmpty()) {
            throw new IllegalStateException(
                    "Missing employee records: " + missingCodes
            );
        }

        // Fetch existing agent registrations.
        List<EmployeeAgent> existingAgents =
                employeeAgentRepository.findAllByEmployeeCodeIn(
                        REQUIRED_EMPLOYEE_CODES
                );

        Map<String, EmployeeAgent> existingByCode = new LinkedHashMap<>();

        for (EmployeeAgent existingAgent : existingAgents) {
            existingByCode.put(
                    existingAgent.getEmployeeCode(),
                    existingAgent
            );
        }

        List<EmployeeAgent> agentsToCreate = new ArrayList<>();

        List<EmployeeAgentRegistrationItem> registrationItems =
                new ArrayList<>();

        int alreadyRegisteredCount = 0;

        // Prepare registrations.
        for (String employeeCode : REQUIRED_EMPLOYEE_CODES) {

            ExtractedRecord sourceRecord =
                    recordsByEmployeeCode.get(employeeCode);

            String agentKey = createAgentKey(employeeCode);

            JsonNode employeeData =
                    sourceRecord.getExtractedData().path("data");

            EmployeeAgent existingAgent = existingByCode.get(employeeCode);

            if (existingAgent != null) {

                if (!existingAgent.getSourceRecord().getId()
                        .equals(sourceRecord.getId())) {

                    throw new IllegalStateException(
                            "Existing registration for " + employeeCode
                                    + " points to a different source record"
                    );
                }

                if (!existingAgent.getAgentKey().equals(agentKey)) {
                    throw new IllegalStateException(
                            "Existing agent key does not match expected key for "
                                    + employeeCode
                    );
                }

                // Preserve existing persona settings and synchronize
                // employee information from the source record.
                Map<String, Object> config =
                        existingAgent.getPersonaConfig() == null
                                ? new LinkedHashMap<>()
                                : new LinkedHashMap<>(
                                existingAgent.getPersonaConfig()
                        );

                addEmployeeContext(config, employeeData);

                existingAgent.setPersonaConfig(config);

                alreadyRegisteredCount++;

                registrationItems.add(
                        new EmployeeAgentRegistrationItem(
                                employeeCode,
                                agentKey,
                                "ALREADY_REGISTERED"
                        )
                );

                continue;
            }

            // Ensure the agent key is not already assigned.
            if (employeeAgentRepository.existsByAgentKey(agentKey)) {
                throw new IllegalStateException(
                        "Agent key is already assigned: " + agentKey
                );
            }

            EmployeeAgent newAgent = EmployeeAgent.builder()
                    .sourceRecord(sourceRecord)
                    .employeeCode(employeeCode)
                    .agentKey(agentKey)
                    .personaConfig(createPersonaConfig(employeeData))
                    .enabled(true)
                    .build();

            agentsToCreate.add(newAgent);

            registrationItems.add(
                    new EmployeeAgentRegistrationItem(
                            employeeCode,
                            agentKey,
                            "CREATED"
                    )
            );
        }

        // Persist all new agents in one transaction.
        // Existing agents are updated through JPA dirty checking.
        employeeAgentRepository.saveAll(agentsToCreate);

        return new EmployeeAgentRegistrationResponse(
                REQUIRED_EMPLOYEE_CODES.size(),
                sourceRecords.size(),
                agentsToCreate.size(),
                alreadyRegisteredCount,
                List.copyOf(registrationItems)
        );
    }

    private void validateEmployeeRecord(
            ExtractedRecord sourceRecord,
            JsonNode data,
            String employeeCode
    ) {

        if (employeeCode == null || employeeCode.isBlank()) {
            throw new IllegalStateException(
                    "Employee code is missing in source record "
                            + sourceRecord.getId()
            );
        }

        requireField(data, "Full Name", employeeCode);
        requireField(data, "Title", employeeCode);
        requireField(data, "Department", employeeCode);
    }

    private void requireField(
            JsonNode data,
            String fieldName,
            String employeeCode
    ) {

        String value = readText(data, fieldName);

        if (value == null || value.isBlank()) {
            throw new IllegalStateException(
                    "Missing " + fieldName + " for employee " + employeeCode
            );
        }
    }

    private String readText(JsonNode data, String fieldName) {

        JsonNode value = data.path(fieldName);

        if (value.isMissingNode() || value.isNull()) {
            return null;
        }

        return value.asText();
    }

    private String createAgentKey(String employeeCode) {
        return "agent-" + employeeCode.toLowerCase(Locale.ROOT);
    }

    private Map<String, Object> createPersonaConfig(JsonNode data) {

        Map<String, Object> config = new LinkedHashMap<>();

        config.put("responseStyle", "professional");
        config.put("evidencePolicy", "grounded");
        config.put("assumptionsAllowed", true);
        config.put("assumptionsMustBeDisclosed", true);

        addEmployeeContext(config, data);

        return config;
    }

    private void addEmployeeContext(
            Map<String, Object> config,
            JsonNode data
    ) {

        config.put("employeeCode", readText(data, "Emp ID"));
        config.put("fullName", readText(data, "Full Name"));
        config.put("designation", readText(data, "Title"));
        config.put("department", readText(data, "Department"));
        config.put("employmentStatus", readText(data, "Status"));
    }
}
