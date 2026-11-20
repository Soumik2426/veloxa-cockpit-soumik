
package com.veloxa.cockpit.employeeagent.repository;

import java.util.List;
import java.util.Optional;
import java.util.UUID;

import com.veloxa.cockpit.employeeagent.entity.AgentConversation;
import com.veloxa.cockpit.employeeagent.enums.ConversationStatus;

import org.springframework.data.jpa.repository.JpaRepository;

public interface AgentConversationRepository extends JpaRepository<AgentConversation, UUID> {

    List<AgentConversation> findAllByAgent_EmployeeCodeOrderByUpdatedAtDesc(
            String employeeCode
    );

    List<AgentConversation> findAllByAgent_EmployeeCodeAndStatusOrderByUpdatedAtDesc(
            String employeeCode,
            ConversationStatus status
    );

    Optional<AgentConversation> findByIdAndAgent_EmployeeCode(
            UUID conversationId,
            String employeeCode
    );

    List<AgentConversation> findAllByAgent_IdOrderByUpdatedAtDesc(
            UUID agentId
    );
}
