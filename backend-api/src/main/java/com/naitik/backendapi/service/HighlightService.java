package com.naitik.backendapi.service;

import com.naitik.backendapi.dto.HighlightRequest;
import com.naitik.backendapi.entity.Highlight;
import com.naitik.backendapi.repository.HighlightRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import java.time.Instant;
import java.util.List;

@Service
@RequiredArgsConstructor
public class HighlightService {

    private final HighlightRepository highlightRepository;

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

                return highlightRepository.save(highlight);
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
}