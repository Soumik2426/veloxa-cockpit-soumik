package com.veloxa.cockpit.agent;

import java.util.Map;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest;
import org.springframework.test.context.bean.override.mockito.MockitoBean;
import org.springframework.test.web.servlet.MockMvc;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.argThat;
import static org.mockito.Mockito.doThrow;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;
import static org.springframework.http.MediaType.APPLICATION_JSON;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

@WebMvcTest(AgentController.class)
class AgentControllerTest {

    @Autowired
    private MockMvc mockMvc;

    @MockitoBean
    private AgentService agentService;

    @Test
    void validatesQuestionAndReturnsAgentResponse() throws Exception {
        when(agentService.ask(any())).thenReturn(Map.of(
                "question", "Summarize delivery risks.",
                "answer", "Review the cited risks [RAG-1].",
                "retrieval_sources", new String[]{"rag"},
                "evidence", new Object[]{Map.of("evidence_id", "RAG-1")},
                "confidence", Map.of("level", "moderate", "rationale", "One source."),
                "limitations", new String[]{}));

        mockMvc.perform(post("/api/v1/agent/ask")
                        .contentType(APPLICATION_JSON)
                        .content("{\"question\":\"Summarize delivery risks.\"}"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.answer").value("Review the cited risks [RAG-1]."))
                .andExpect(jsonPath("$.retrieval_sources[0]").value("rag"));

        verify(agentService).ask(argThat(request ->
                request.question().equals("Summarize delivery risks.")));
    }

    @Test
    void rejectsBlankQuestionWithoutCallingPythonService() throws Exception {
        mockMvc.perform(post("/api/v1/agent/ask")
                        .contentType(APPLICATION_JSON)
                        .content("{\"question\":\"   \"}"))
                .andExpect(status().isBadRequest());

        verify(agentService, org.mockito.Mockito.never()).ask(any());
    }

    @Test
    void mapsForwardingFailureToGatewayError() throws Exception {
        doThrow(new org.springframework.web.server.ResponseStatusException(
                org.springframework.http.HttpStatus.BAD_GATEWAY,
                "The AI service could not complete the request."))
                .when(agentService).ask(any());

        mockMvc.perform(post("/api/v1/agent/ask")
                        .contentType(APPLICATION_JSON)
                        .content("{\"question\":\"Summarize delivery risks.\"}"))
                .andExpect(status().isBadGateway());
    }
}
