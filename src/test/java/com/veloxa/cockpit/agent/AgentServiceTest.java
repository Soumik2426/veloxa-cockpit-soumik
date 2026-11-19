package com.veloxa.cockpit.agent;

import com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.jupiter.api.Test;
import org.springframework.http.MediaType;
import org.springframework.test.web.client.MockRestServiceServer;
import org.springframework.web.client.RestClient;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.springframework.http.HttpMethod.POST;
import static org.springframework.test.web.client.MockRestServiceServer.bindTo;
import static org.springframework.test.web.client.match.MockRestRequestMatchers.content;
import static org.springframework.test.web.client.match.MockRestRequestMatchers.method;
import static org.springframework.test.web.client.match.MockRestRequestMatchers.requestTo;
import static org.springframework.test.web.client.response.MockRestResponseCreators.withSuccess;

class AgentServiceTest {

    @Test
    void postsQuestionToPythonAgentAndReturnsItsResponse() {

        RestClient.Builder builder = RestClient.builder();
        MockRestServiceServer server = bindTo(builder).build();

        AgentService service = new AgentService(
                builder,
                new ObjectMapper(),
                "http://python-ai.test"
        );

        server.expect(requestTo("http://python-ai.test/api/v1/agent/ask"))
                .andExpect(method(POST))
                .andExpect(content().contentType(MediaType.APPLICATION_JSON))
                .andExpect(content().json(
                        "{\"question\":\"What is delayed?\"}"
                ))
                .andRespond(withSuccess("""
                        {
                          "question": "What is delayed?",
                          "answer": "The project is delayed.",
                          "retrieval_sources": ["sql"],
                          "evidence": [],
                          "confidence": {
                            "level": "moderate",
                            "rationale": "One source."
                          },
                          "limitations": []
                        }
                        """, MediaType.APPLICATION_JSON));

        var response = service.ask(
                new AgentController.AskRequest("What is delayed?")
        );

        assertEquals("The project is delayed.", response.get("answer"));
        server.verify();
    }
}
