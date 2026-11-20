
package com.veloxa.cockpit.employeeagent.entity;

import com.veloxa.cockpit.employeeagent.enums.MessageRole;
import jakarta.persistence.*;
import lombok.Getter;
import org.hibernate.annotations.JdbcTypeCode;
import org.hibernate.type.SqlTypes;

import java.time.OffsetDateTime;
import java.util.Map;
import java.util.UUID;

@Entity
@Table(name = "agent_messages")
@Getter
public class AgentMessage {

    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    private UUID id;

    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "conversation_id", nullable = false)
    private AgentConversation conversation;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false, length = 20)
    private MessageRole role;

    @Column(nullable = false, columnDefinition = "TEXT")
    private String content;

    @JdbcTypeCode(SqlTypes.JSON)
    @Column(columnDefinition = "jsonb")
    private Map<String, Object> citations;

    @JdbcTypeCode(SqlTypes.JSON)
    @Column(columnDefinition = "jsonb")
    private Map<String, Object> metadata;

    @Column(nullable = false, updatable = false)
    private OffsetDateTime createdAt;

    protected AgentMessage() {
        // Required by JPA
    }

    private AgentMessage(
            AgentConversation conversation,
            MessageRole role,
            String content,
            Map<String, Object> citations,
            Map<String, Object> metadata
    ) {
        this.conversation = conversation;
        this.role = role;
        this.content = content;
        this.citations = citations;
        this.metadata = metadata;
        this.createdAt = OffsetDateTime.now();
    }

    public static AgentMessage create(
            AgentConversation conversation,
            MessageRole role,
            String content,
            Map<String, Object> citations,
            Map<String, Object> metadata
    ) {
        return new AgentMessage(
                conversation,
                role,
                content,
                citations,
                metadata
        );
    }
}