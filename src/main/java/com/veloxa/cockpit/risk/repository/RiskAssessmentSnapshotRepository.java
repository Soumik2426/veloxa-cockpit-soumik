package com.veloxa.cockpit.risk.repository;

import java.time.LocalDate;
import java.util.Optional;
import java.util.UUID;

import com.veloxa.cockpit.risk.entity.RiskAssessmentSnapshot;

import org.springframework.data.jpa.repository.JpaRepository;

public interface RiskAssessmentSnapshotRepository
        extends JpaRepository<RiskAssessmentSnapshot, UUID> {

    Optional<RiskAssessmentSnapshot> findByAssessmentDate(
            LocalDate assessmentDate
    );

    Optional<RiskAssessmentSnapshot>
    findTopByOrderByAssessmentDateDescUpdatedAtDesc();
}
