package com.naitik.backendapi.service;

import com.naitik.backendapi.dto.HighlightRequest;
import com.naitik.backendapi.entity.Highlight;
import com.naitik.backendapi.repository.HighlightRepository;
import io.micrometer.core.instrument.Counter;
import io.micrometer.core.instrument.MeterRegistry;
import org.springframework.stereotype.Service;

import java.time.Instant;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;

@Service
public class HighlightService {

    private final HighlightRepository highlightRepository;
    private final ScoreEventService scoreEventService;
    private final Counter highlightsSavedCounter;

    public HighlightService(
            HighlightRepository highlightRepository,
            ScoreEventService scoreEventService,
            MeterRegistry meterRegistry
    ) {
        this.highlightRepository = highlightRepository;
        this.scoreEventService = scoreEventService;
        this.highlightsSavedCounter = Counter.builder("sports_highlights_saved_total")
                .description("Total number of highlights saved")
                .register(meterRegistry);
    }

    public Highlight saveHighlight(HighlightRequest request) {
        return highlightRepository.findByClipFile(request.getClipFile())
                .orElseGet(() -> {
                    Highlight highlight = new Highlight();
                    highlight.setClipFile(request.getClipFile());
                    highlight.setClipPath(request.getClipPath());
                    highlight.setEventTimestamp(request.getEventTimestamp());
                    highlight.setClock(request.getClock());
                    highlight.setOldScore(request.getOldScore());
                    highlight.setNewScore(request.getNewScore());
                    highlight.setClipStartTime(request.getStartTime());
                    highlight.setDuration(request.getDuration());
                    highlight.setCreatedAt(Instant.now());

                    Highlight saved = highlightRepository.save(highlight);
                    highlightsSavedCounter.increment();
                    return saved;
                });
    }

    public List<Highlight> getAllHighlights() {
        return highlightRepository.findAllByOrderByEventTimestampAsc();
    }

    public List<Highlight> getLatestHighlights() {
        return highlightRepository.findTop10ByOrderByCreatedAtDesc();
    }

    public long getHighlightCount() {
        return highlightRepository.count();
    }

    public List<Highlight> getLatestUniqueHighlights() {
        List<Highlight> allHighlights = highlightRepository.findTop10ByOrderByCreatedAtDesc();
        Map<String, Highlight> uniqueHighlights = new LinkedHashMap<>();

        for (Highlight highlight : allHighlights) {
            String key = highlight.getClock() + "|" + highlight.getOldScore() + "|" + highlight.getNewScore();
            if (!uniqueHighlights.containsKey(key)) {
                uniqueHighlights.put(key, highlight);
            }
        }

        return new ArrayList<>(uniqueHighlights.values());
    }

    public long getLatestUniqueHighlightCount() {
        return getLatestUniqueHighlights().size();
    }

    public Optional<Highlight> getHighlightById(Long id) {
        return highlightRepository.findById(id);
    }

    public void deleteHighlightAndMatchingEvent(Long highlightId) {
        Highlight highlight = highlightRepository.findById(highlightId)
                .orElseThrow(() -> new RuntimeException("Highlight not found"));

        String clock = highlight.getClock();
        String oldScore = highlight.getOldScore();
        String newScore = highlight.getNewScore();

        highlightRepository.delete(highlight);
        scoreEventService.deleteMatchingEvents(clock, oldScore, newScore);
    }
}