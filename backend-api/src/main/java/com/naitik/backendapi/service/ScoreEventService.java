package com.naitik.backendapi.service;

import com.naitik.backendapi.dto.ScoreEventMessage;
import com.naitik.backendapi.entity.ScoreEvent;
import com.naitik.backendapi.repository.ScoreEventRepository;
import io.micrometer.core.instrument.Counter;
import io.micrometer.core.instrument.MeterRegistry;
import org.springframework.stereotype.Service;

import java.time.Instant;
import java.util.List;

@Service
public class ScoreEventService {
    private final ScoreEventRepository scoreEventRepository;
    private final Counter scoreEventsConsumedCounter;

    public ScoreEventService(ScoreEventRepository scoreEventRepository, MeterRegistry meterRegistry) {
        this.scoreEventRepository = scoreEventRepository;
        this.scoreEventsConsumedCounter = Counter.builder("sports_score_events_consumed_total")
                .description("Total number of score events consumed and saved")
                .register(meterRegistry);
    }

    public ScoreEvent saveFromMessage(ScoreEventMessage message) {
        ScoreEvent event = new ScoreEvent();
        event.setEventType(message.getEventType());
        event.setVideoTimestamp(message.getTimestamp());
        event.setClock(message.getClock());
        event.setOldScore(message.getOldScore());
        event.setNewScore(message.getNewScore());
        event.setFile(message.getFile());
        event.setCreatedAt(Instant.now());

        ScoreEvent savedEvent = scoreEventRepository.save(event);
        scoreEventsConsumedCounter.increment();

        return savedEvent;
    }

    public List<ScoreEvent> getAllEvents() {
        return scoreEventRepository.findAllByOrderByVideoTimestampAsc();
    }

    public List<ScoreEvent> getLatestEvents() {
        return scoreEventRepository.findTop10ByOrderByCreatedAtDesc();
    }

    public ScoreEvent getLatestEventRecord() {
        return scoreEventRepository.findTop10ByOrderByCreatedAtDesc()
                .stream()
                .findFirst()
                .orElse(null);
    }
}