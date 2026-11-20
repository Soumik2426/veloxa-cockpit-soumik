package com.veloxa.cockpit.risk.service;

import java.time.LocalDate;
import java.time.OffsetDateTime;
import java.time.ZoneId;
import java.time.Duration;

import com.veloxa.cockpit.risk.dto.RiskAssessmentResponse;
import com.veloxa.cockpit.risk.entity.RiskAssessmentSnapshot;
import com.veloxa.cockpit.risk.repository.RiskAssessmentSnapshotRepository;

import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.core.task.TaskExecutor;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Service;

@Service
public class RiskAssessmentService {

    private static final ZoneId BUSINESS_ZONE = ZoneId.of("Asia/Kolkata");
    private static final Object REFRESH_LOCK = new Object();

    private final RiskAssessmentSnapshotRepository snapshotRepository;
    private final RiskAssessmentGenerationService generationService;
    private final TaskExecutor taskExecutor;
    private final JdbcTemplate jdbcTemplate;

    public RiskAssessmentService(
            RiskAssessmentSnapshotRepository snapshotRepository,
            RiskAssessmentGenerationService generationService,
            @Qualifier("riskTaskExecutor") TaskExecutor taskExecutor,
            JdbcTemplate jdbcTemplate
    ) {
        this.snapshotRepository = snapshotRepository;
        this.generationService = generationService;
        this.taskExecutor = taskExecutor;
        this.jdbcTemplate = jdbcTemplate;
    }

    public RiskAssessmentResponse latest() {
        return snapshotRepository
                .findTopByOrderByAssessmentDateDescUpdatedAtDesc()
                .map(this::recoverStaleSnapshot)
                .orElseGet(() -> new RiskAssessmentResponse(
                        null,
                        null,
                        null,
                        null,
                        "NOT_STARTED",
                        null,
                        null,
                        null
                ));
    }

    public RiskAssessmentResponse requestRefresh(boolean scheduled) {
        synchronized (REFRESH_LOCK) {
            LocalDate assessmentDate = LocalDate.now(BUSINESS_ZONE);
            String dataVersion = currentDataVersion();

            RiskAssessmentSnapshot snapshot = snapshotRepository
                    .findByAssessmentDate(assessmentDate)
                    .orElseGet(() -> newSnapshot(assessmentDate));

            if ("RUNNING".equals(snapshot.getStatus())) {
                if (!isStale(snapshot)) {
                    return toResponse(snapshot);
                }

                snapshot.setStatus("FAILED");
                snapshot.setErrorMessage(
                        "The previous risk assessment was interrupted and can be retried."
                );
                snapshot.setUpdatedAt(now());
            }

            if (scheduled
                    && "COMPLETED".equals(snapshot.getStatus())
                    && dataVersion.equals(snapshot.getDataVersion())) {
                return toResponse(snapshot);
            }

            snapshot.setStatus("RUNNING");
            snapshot.setUpdatedAt(now());
            snapshot.setDataVersion(dataVersion);
            snapshot.setErrorMessage(null);
            snapshot = snapshotRepository.save(snapshot);

            RiskAssessmentSnapshot queuedSnapshot = snapshot;
            try {
                taskExecutor.execute(
                        () -> generationService.generate(queuedSnapshot.getId())
                );
            } catch (RuntimeException exception) {
                queuedSnapshot.setStatus("FAILED");
                queuedSnapshot.setErrorMessage(
                        "The risk assessment could not be queued."
                );
                queuedSnapshot.setUpdatedAt(now());
                snapshotRepository.save(queuedSnapshot);
            }

            return toResponse(snapshot);
        }
    }

    @Scheduled(cron = "${risk.assessment.cron:0 0 2 * * *}")
    public void refreshDailyAssessment() {
        requestRefresh(true);
    }

    private RiskAssessmentSnapshot newSnapshot(LocalDate assessmentDate) {
        RiskAssessmentSnapshot snapshot = new RiskAssessmentSnapshot();
        snapshot.setAssessmentDate(assessmentDate);
        snapshot.setStatus("NOT_STARTED");
        snapshot.setUpdatedAt(now());
        return snapshot;
    }

    private String currentDataVersion() {
        return jdbcTemplate.queryForObject(
                "SELECT COALESCE(MAX(processed_at)::text, 'unknown') FROM ingestion_file",
                String.class
        );
    }

    private OffsetDateTime now() {
        return OffsetDateTime.now(BUSINESS_ZONE);
    }

    private boolean isStale(RiskAssessmentSnapshot snapshot) {
        return snapshot.getUpdatedAt() == null
                || Duration.between(snapshot.getUpdatedAt(), now())
                .compareTo(Duration.ofMinutes(15)) > 0;
    }

    private RiskAssessmentResponse recoverStaleSnapshot(
            RiskAssessmentSnapshot snapshot
    ) {
        if ("RUNNING".equals(snapshot.getStatus()) && isStale(snapshot)) {
            snapshot.setStatus("FAILED");
            snapshot.setErrorMessage(
                    "The previous risk assessment was interrupted and can be retried."
            );
            snapshot.setUpdatedAt(now());
            snapshot = snapshotRepository.save(snapshot);
        }

        return toResponse(snapshot);
    }

    private RiskAssessmentResponse toResponse(
            RiskAssessmentSnapshot snapshot
    ) {
        return new RiskAssessmentResponse(
                snapshot.getId(),
                snapshot.getAssessmentDate(),
                snapshot.getGeneratedAt(),
                snapshot.getUpdatedAt(),
                snapshot.getStatus(),
                snapshot.getAssessment(),
                snapshot.getDataVersion(),
                snapshot.getErrorMessage()
        );
    }
}
