package com.naitik.backendapi.service;

import com.naitik.backendapi.dto.ScoreEventMessage;
import com.naitik.backendapi.entity.ScoreEvent;
import com.naitik.backendapi.repository.ScoreEventRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import java.time.Instant;
import java.util.List;

@Service
@RequiredArgsConstructor
public class ScoreEventService {
    private final ScoreEventRepository scoreEventRepository;

    public ScoreEvent saveFromMessage(ScoreEventMessage message) {
        ScoreEvent event = new ScoreEvent();
        event.setEventType(message.getEventType());
        event.setVideoTimestamp(message.getTimestamp());
        event.setClock(message.getClock());
        event.setOldScore(message.getOldScore());
        event.setNewScore(message.getNewScore());
        event.setFile(message.getFile());
        event.setCreatedAt(Instant.now());
        return scoreEventRepository.save(event);
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