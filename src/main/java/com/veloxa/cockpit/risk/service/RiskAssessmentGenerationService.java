package com.veloxa.cockpit.risk.service;

import java.time.OffsetDateTime;
import java.util.UUID;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.veloxa.cockpit.agent.AgentController;
import com.veloxa.cockpit.agent.AgentService;
import com.veloxa.cockpit.risk.entity.RiskAssessmentSnapshot;
import com.veloxa.cockpit.risk.repository.RiskAssessmentSnapshotRepository;

import org.springframework.stereotype.Service;

@Service
public class RiskAssessmentGenerationService {

    private final RiskAssessmentSnapshotRepository snapshotRepository;
    private final AgentService agentService;
    private final ObjectMapper objectMapper;

    public RiskAssessmentGenerationService(
            RiskAssessmentSnapshotRepository snapshotRepository,
            AgentService agentService,
            ObjectMapper objectMapper
    ) {
        this.snapshotRepository = snapshotRepository;
        this.agentService = agentService;
        this.objectMapper = objectMapper;
    }

    public void generate(UUID snapshotId) {
        RiskAssessmentSnapshot snapshot = snapshotRepository
                .findById(snapshotId)
                .orElse(null);

        if (snapshot == null || !"RUNNING".equals(snapshot.getStatus())) {
            return;
        }

        try {
            var response = agentService.ask(
                    new AgentController.AskRequest(RISK_QUESTION)
            );

            snapshot.setAssessment(objectMapper.valueToTree(response));
            snapshot.setGeneratedAt(OffsetDateTime.now());
            snapshot.setUpdatedAt(OffsetDateTime.now());
            snapshot.setStatus("COMPLETED");
            snapshot.setErrorMessage(null);
            snapshotRepository.save(snapshot);
        } catch (Exception exception) {
            snapshot.setUpdatedAt(OffsetDateTime.now());
            snapshot.setStatus("FAILED");
            snapshot.setErrorMessage(
                    exception.getMessage() == null
                            ? "Risk assessment generation failed."
                            : exception.getMessage()
            );
            snapshotRepository.save(snapshot);
        }
    }

    private static final String RISK_QUESTION = """
            Analyse the company's current business risks using the available company records
            and documents.

            Identify major business, personnel, engineering, product, financial,
            hiring and operational risks. Explain potential impact, cite supporting
            evidence, distinguish confirmed evidence from assumptions, identify the
            top concerns for the CEO, and disclose information gaps. Do not invent
            risk scores, dates, facts or evidence.
            """;
}
