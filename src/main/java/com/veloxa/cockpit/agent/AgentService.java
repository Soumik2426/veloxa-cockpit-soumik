package com.veloxa.cockpit.agent;

import java.util.Map;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.core.ParameterizedTypeReference;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestClient;
import org.springframework.web.client.RestClientException;
import org.springframework.web.server.ResponseStatusException;

@Service
public class AgentService {

    private static final ParameterizedTypeReference<Map<String, Object>> RESPONSE_TYPE =
            new ParameterizedTypeReference<>() {};

    private final RestClient aiServiceClient;

    public AgentService(
            RestClient.Builder restClientBuilder,
            @Value("${ai-service.url:http://localhost:8000}") String aiServiceUrl) {
        this.aiServiceClient = restClientBuilder.baseUrl(aiServiceUrl).build();
    }

    public Map<String, Object> ask(AgentController.AskRequest request) {
        try {
            return aiServiceClient.post()
                    .uri("/api/v1/agent/ask")
                    .body(request)
                    .retrieve()
                    .body(RESPONSE_TYPE);
        } catch (RestClientException exception) {
            throw new ResponseStatusException(
                    HttpStatus.BAD_GATEWAY,
                    "The AI service could not complete the request.",
                    exception);
        }
    }
}
