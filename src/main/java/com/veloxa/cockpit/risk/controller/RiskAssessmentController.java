package com.veloxa.cockpit.risk.controller;

import com.veloxa.cockpit.risk.dto.RiskAssessmentResponse;
import com.veloxa.cockpit.risk.service.RiskAssessmentService;

import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/v1/risk-assessments")
public class RiskAssessmentController {

    private final RiskAssessmentService riskAssessmentService;

    public RiskAssessmentController(
            RiskAssessmentService riskAssessmentService
    ) {
        this.riskAssessmentService = riskAssessmentService;
    }

    @GetMapping("/latest")
    public RiskAssessmentResponse latest() {
        return riskAssessmentService.latest();
    }

    @PostMapping("/refresh")
    public ResponseEntity<RiskAssessmentResponse> refresh() {
        return ResponseEntity.accepted()
                .body(riskAssessmentService.requestRefresh(false));
    }
}
