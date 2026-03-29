package com.naitik.backendapi.kafka;

import tools.jackson.databind.ObjectMapper;
import com.naitik.backendapi.dto.ScoreEventMessage;
import com.naitik.backendapi.service.ScoreEventService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.kafka.annotation.KafkaListener;
import org.springframework.stereotype.Component;

@Component
@RequiredArgsConstructor
@Slf4j
public class ScoreEventConsumer {

    private final ObjectMapper objectMapper;
    private final ScoreEventService scoreEventService;

    @Value("${app.kafka.topic.score-events}")
    private String topicName;

    @KafkaListener(topics = "${app.kafka.topic.score-events}", groupId = "sports-backend-group")
    public void consume(String message) {
        try {
            ScoreEventMessage eventMessage = objectMapper.readValue(message, ScoreEventMessage.class);
            scoreEventService.saveFromMessage(eventMessage);
            log.info("Consumed and saved score event from topic {}: {}", topicName, eventMessage.getNewScore());
        } catch (Exception error) {
            log.error("Failed to consume Kafka message: {}", message, error);
        }
    }
}