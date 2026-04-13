package com.naitik.backendapi.controller;

import com.naitik.backendapi.entity.Highlight;
import com.naitik.backendapi.entity.ScoreEvent;
import com.naitik.backendapi.service.HighlightService;
import com.naitik.backendapi.service.ScoreEventService;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/events")
@RequiredArgsConstructor
@CrossOrigin(origins = "*")
public class ScoreEventController {
    private final ScoreEventService scoreEventService;
    private final HighlightService highlightService;

    @GetMapping
    public List<ScoreEvent> getAllEvents() {
        List<Highlight> highlights = highlightService.getLatestUniqueHighlights();
        return scoreEventService.getEventsWithHighlights(highlights);
    }

    @GetMapping("/latest")
    public List<ScoreEvent> getLatestEvents() {
        List<Highlight> highlights = highlightService.getLatestUniqueHighlights();
        return scoreEventService.getEventsWithHighlights(highlights);
    }
}