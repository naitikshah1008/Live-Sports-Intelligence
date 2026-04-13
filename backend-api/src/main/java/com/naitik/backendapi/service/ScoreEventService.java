package com.naitik.backendapi.service;

import com.naitik.backendapi.dto.ScoreEventMessage;
import com.naitik.backendapi.entity.ScoreEvent;
import com.naitik.backendapi.repository.ScoreEventRepository;
import io.micrometer.core.instrument.Counter;
import io.micrometer.core.instrument.MeterRegistry;
import org.springframework.stereotype.Service;

import java.time.Instant;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import com.naitik.backendapi.entity.Highlight;

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
        return scoreEventRepository.findTopByOrderByCreatedAtDesc().orElse(null);
    }

    public List<ScoreEvent> getLatestUniqueEvents() {
        List<ScoreEvent> allEvents = scoreEventRepository.findAllByOrderByCreatedAtDesc();
        Map<String, ScoreEvent> uniqueEvents = new LinkedHashMap<>();
        for (ScoreEvent event : allEvents) {
            String key = event.getClock() + "|" + event.getOldScore() + "|" + event.getNewScore();
            if (!uniqueEvents.containsKey(key)) {
                uniqueEvents.put(key, event);
            }
        }
        return new ArrayList<>(uniqueEvents.values());
    }

    public ScoreEvent getLatestValidUniqueEvent() {
        List<ScoreEvent> uniqueEvents = getLatestUniqueEvents();
        return uniqueEvents.isEmpty() ? null : uniqueEvents.get(0);
    }

    public void deleteMatchingEvents(String clock, String oldScore, String newScore) {
        List<ScoreEvent> matchingEvents = scoreEventRepository.findByClockAndOldScoreAndNewScore(clock, oldScore, newScore);
        scoreEventRepository.deleteAll(matchingEvents);
    }

    public List<ScoreEvent> getEventsWithHighlights(List<Highlight> highlights) {
        List<ScoreEvent> allEvents = scoreEventRepository.findAllByOrderByCreatedAtDesc();
        Map<String, Highlight> highlightMap = new LinkedHashMap<>();
        for (Highlight highlight : highlights) {
            String key = highlight.getClock() + "|" + highlight.getOldScore() + "|" + highlight.getNewScore();
            highlightMap.put(key, highlight);
        }
        Map<String, ScoreEvent> uniqueEvents = new LinkedHashMap<>();
        for (ScoreEvent event : allEvents) {
            String key = event.getClock() + "|" + event.getOldScore() + "|" + event.getNewScore();
            if (highlightMap.containsKey(key) && !uniqueEvents.containsKey(key)) {
                uniqueEvents.put(key, event);
            }
        }
        return new ArrayList<>(uniqueEvents.values());
    }
}