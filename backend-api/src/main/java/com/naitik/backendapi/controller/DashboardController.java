package com.naitik.backendapi.controller;

import com.naitik.backendapi.dto.DashboardSummaryResponse;
import com.naitik.backendapi.entity.ScoreEvent;
import com.naitik.backendapi.service.HighlightService;
import com.naitik.backendapi.service.ScoreEventService;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/dashboard")
@RequiredArgsConstructor
@CrossOrigin(origins = "*")
public class DashboardController {
    private final ScoreEventService scoreEventService;
    private final HighlightService highlightService;
    @GetMapping("/summary")
    public DashboardSummaryResponse getSummary() {
        ScoreEvent latestEvent = scoreEventService.getLatestEventRecord();
        String latestClock = latestEvent != null ? latestEvent.getClock() : "-";
        String latestScore = latestEvent != null ? latestEvent.getNewScore() : "-";
        String latestEventText = latestEvent != null
                ? latestEvent.getOldScore() + " -> " + latestEvent.getNewScore()
                : "No events yet";
        return DashboardSummaryResponse.builder()
                .latestClock(latestClock)
                .latestScore(latestScore)
                .latestEvent(latestEventText)
                .totalEvents(scoreEventService.getAllEvents().size())
                .totalHighlights(highlightService.getHighlightCount())
                .build();
    }
}