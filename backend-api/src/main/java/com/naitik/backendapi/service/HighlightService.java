package com.naitik.backendapi.service;

import com.naitik.backendapi.dto.HighlightRequest;
import com.naitik.backendapi.entity.Highlight;
import com.naitik.backendapi.repository.HighlightRepository;
import com.naitik.backendapi.repository.PipelineRunRepository;
import com.naitik.backendapi.repository.SportMatchRepository;
import io.micrometer.core.instrument.Counter;
import io.micrometer.core.instrument.MeterRegistry;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

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
    private final SportMatchRepository sportMatchRepository;
    private final PipelineRunRepository pipelineRunRepository;
    private final Counter highlightsSavedCounter;

    public HighlightService(
            HighlightRepository highlightRepository,
            ScoreEventService scoreEventService,
            SportMatchRepository sportMatchRepository,
            PipelineRunRepository pipelineRunRepository,
            MeterRegistry meterRegistry
    ) {
        this.highlightRepository = highlightRepository;
        this.scoreEventService = scoreEventService;
        this.sportMatchRepository = sportMatchRepository;
        this.pipelineRunRepository = pipelineRunRepository;
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
                    attachMatchAndRun(highlight, request.getMatchId(), request.getPipelineRunId());

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

    @Transactional
    public boolean deleteHighlightAndMatchingEvent(Long highlightId) {
        Optional<Highlight> existingHighlight = highlightRepository.findById(highlightId);
        if (existingHighlight.isEmpty()) {
            return false;
        }

        Highlight highlight = existingHighlight.get();
        String clock = highlight.getClock();
        String oldScore = highlight.getOldScore();
        String newScore = highlight.getNewScore();
        Double eventTimestamp = highlight.getEventTimestamp();

        highlightRepository.delete(highlight);
        scoreEventService.deleteMatchingEvent(clock, oldScore, newScore, eventTimestamp);
        return true;
    }

    private void attachMatchAndRun(Highlight highlight, Long matchId, Long pipelineRunId) {
        if (matchId != null) {
            sportMatchRepository.findById(matchId).ifPresent(highlight::setMatch);
        }
        if (pipelineRunId != null) {
            pipelineRunRepository.findById(pipelineRunId)
                    .ifPresent(run -> {
                        highlight.setPipelineRun(run);
                        if (highlight.getMatch() == null) {
                            highlight.setMatch(run.getMatch());
                        }
                    });
        }
    }
}
