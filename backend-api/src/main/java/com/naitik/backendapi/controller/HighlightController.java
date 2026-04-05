package com.naitik.backendapi.controller;

import com.naitik.backendapi.dto.HighlightRequest;
import com.naitik.backendapi.entity.Highlight;
import com.naitik.backendapi.service.HighlightService;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/highlights")
@RequiredArgsConstructor
@CrossOrigin(origins = "*")
public class HighlightController {

    private final HighlightService highlightService;

    @PostMapping
    public Highlight createHighlight(@RequestBody HighlightRequest request) {
        return highlightService.saveHighlight(request);
    }

    @GetMapping
    public List<Highlight> getAllHighlights() {
        return highlightService.getAllHighlights();
    }

    @GetMapping("/latest")
    public List<Highlight> getLatestHighlights() {
        return highlightService.getLatestHighlights();
    }
}