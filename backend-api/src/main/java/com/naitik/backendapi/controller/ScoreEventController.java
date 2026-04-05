package com.naitik.backendapi.controller;

import com.naitik.backendapi.entity.ScoreEvent;
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

    @GetMapping
    public List<ScoreEvent> getAllEvents() {
        return scoreEventService.getAllEvents();
    }

    @GetMapping("/latest")
    public List<ScoreEvent> getLatestEvents() {
        return scoreEventService.getLatestEvents();
    }
}