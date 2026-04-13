package com.naitik.backendapi.controller;

import com.naitik.backendapi.dto.HighlightRequest;
import com.naitik.backendapi.entity.Highlight;
import com.naitik.backendapi.service.HighlightService;
import lombok.RequiredArgsConstructor;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.core.io.Resource;
import org.springframework.core.io.UrlResource;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.net.MalformedURLException;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.List;

@RestController
@RequestMapping("/api/highlights")
@RequiredArgsConstructor
@CrossOrigin(origins = "*")
public class HighlightController {
    private final HighlightService highlightService;

    @Value("${app.highlights.clips-dir}")
    private String clipsDir;

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
        return highlightService.getLatestUniqueHighlights();
    }

    @DeleteMapping("/{id}/with-event")
    public ResponseEntity<Void> deleteHighlightWithEvent(@PathVariable Long id) {
        highlightService.deleteHighlightAndMatchingEvent(id);
        return ResponseEntity.noContent().build();
    }

    @GetMapping("/file/{clipFile}")
    public ResponseEntity<Resource> serveHighlightClip(@PathVariable String clipFile) {
        try {
            Path clipPath = Paths.get(clipsDir).resolve(clipFile).normalize();
            Resource resource = new UrlResource(clipPath.toUri());
            if (!resource.exists() || !resource.isReadable()) {
                return ResponseEntity.notFound().build();
            }
            return ResponseEntity.ok()
                    .contentType(MediaType.parseMediaType("video/mp4"))
                    .header(HttpHeaders.CONTENT_DISPOSITION, "inline; filename=\"" + clipFile + "\"")
                    .body(resource);
        } catch (MalformedURLException error) {
            return ResponseEntity.badRequest().build();
        }
    }
}