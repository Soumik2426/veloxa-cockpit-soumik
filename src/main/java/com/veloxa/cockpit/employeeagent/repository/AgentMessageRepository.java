package com.veloxa.cockpit.employeeagent.repository;

import java.util.List;
import java.util.UUID;

import com.veloxa.cockpit.employeeagent.entity.AgentMessage;

import org.springframework.data.jpa.repository.JpaRepository;

public interface AgentMessageRepository
        extends JpaRepository<AgentMessage, UUID> {

    List<AgentMessage> findAllByConversation_IdOrderByCreatedAtAscIdAsc(
            UUID conversationId
    );

    List<AgentMessage> findAllByConversation_IdOrderByCreatedAtDescIdDesc(
            UUID conversationId
    );

    long countByConversation_Id(UUID conversationId);
}
