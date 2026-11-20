
package com.veloxa.cockpit.employeeagent.controller;

import java.util.List;
import java.util.UUID;

import com.veloxa.cockpit.employeeagent.dto.*;

import com.veloxa.cockpit.employeeagent.service.EmployeeAgentConversationService;

import jakarta.validation.Valid;

import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;

import org.springframework.web.bind.annotation.*;

import lombok.RequiredArgsConstructor;

@RestController
@RequiredArgsConstructor
public class EmployeeAgentController {

    private final EmployeeAgentConversationService conversationService;

    @GetMapping("/api/v1/employee-agents")
    public ResponseEntity<List<EmployeeAgentResponse>> getEnabledAgents() {

        return ResponseEntity.ok(
                conversationService.getEnabledAgents()
        );
    }

    @GetMapping("/api/v1/employee-agents/{employeeCode}")
    public ResponseEntity<EmployeeAgentResponse> getAgent(@PathVariable String employeeCode) {

        return ResponseEntity.ok(
                conversationService.getAgent(employeeCode)
        );
    }

    @PostMapping("/api/v1/employee-agents/{employeeCode}/conversations")
    public ResponseEntity<ConversationResponse> createConversation(@PathVariable String employeeCode, @Valid @RequestBody CreateConversationRequest request) {

        ConversationResponse response = conversationService
                .createConversation(employeeCode, request);

        return ResponseEntity
                .status(HttpStatus.CREATED)
                .body(response);
    }

    @GetMapping("/api/v1/employee-agents/{employeeCode}/conversations")
    public ResponseEntity<List<ConversationResponse>> getConversations(@PathVariable String employeeCode) {

        return ResponseEntity.ok(
                conversationService.getConversations(employeeCode)
        );
    }

    @GetMapping("/api/v1/conversations/{conversationId}")
    public ResponseEntity<ConversationResponse> getConversation(@PathVariable UUID conversationId) {

        return ResponseEntity.ok(
                conversationService.getConversation(conversationId)
        );
    }

    @GetMapping("/api/v1/conversations/{conversationId}/messages")
    public ResponseEntity<List<AgentMessageResponse>> getMessages(@PathVariable UUID conversationId) {

        return ResponseEntity.ok(
                conversationService.getMessages(conversationId)
        );
    }

    @PostMapping("/api/v1/conversations/{conversationId}/messages")
    public ResponseEntity<SendAgentMessageResponse> sendMessage(@PathVariable UUID conversationId, @Valid @RequestBody SendAgentMessageRequest request) {
        return ResponseEntity.ok(
                conversationService.sendMessage(conversationId, request)
        );
    }
}
