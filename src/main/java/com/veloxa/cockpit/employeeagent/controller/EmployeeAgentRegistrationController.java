package com.veloxa.cockpit.employeeagent.controller;

import com.veloxa.cockpit.employeeagent.dto.EmployeeAgentRegistrationResponse;
import com.veloxa.cockpit.employeeagent.service.EmployeeAgentRegistrationService;

import lombok.RequiredArgsConstructor;

import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/v1/employee-agents")
@RequiredArgsConstructor
public class EmployeeAgentRegistrationController {

    private final EmployeeAgentRegistrationService registrationService;

    @PostMapping("/register")
    public ResponseEntity<EmployeeAgentRegistrationResponse> registerAgents() {

        EmployeeAgentRegistrationResponse response =
                registrationService.registerAllAgents();

        return ResponseEntity
                .status(HttpStatus.CREATED)
                .body(response);
    }
}