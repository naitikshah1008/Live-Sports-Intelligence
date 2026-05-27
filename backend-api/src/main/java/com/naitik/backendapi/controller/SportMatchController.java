package com.naitik.backendapi.controller;

import com.naitik.backendapi.dto.MatchRequest;
import com.naitik.backendapi.dto.MatchResponse;
import com.naitik.backendapi.dto.MatchStatusRequest;
import com.naitik.backendapi.entity.SportMatch;
import com.naitik.backendapi.service.SportMatchService;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/matches")
@RequiredArgsConstructor
@CrossOrigin(origins = "*")
public class SportMatchController {

    private final SportMatchService sportMatchService;

    @PostMapping
    public ResponseEntity<MatchResponse> createMatch(@RequestBody MatchRequest request) {
        SportMatch match = sportMatchService.createMatch(request);
        return ResponseEntity.status(HttpStatus.CREATED).body(MatchResponse.from(match));
    }

    @GetMapping
    public List<MatchResponse> getMatches() {
        return sportMatchService.getMatches().stream()
                .map(MatchResponse::from)
                .toList();
    }

    @GetMapping("/{id}")
    public ResponseEntity<MatchResponse> getMatch(@PathVariable Long id) {
        return sportMatchService.getMatch(id)
                .map(MatchResponse::from)
                .map(ResponseEntity::ok)
                .orElseGet(() -> ResponseEntity.notFound().build());
    }

    @PatchMapping("/{id}/status")
    public ResponseEntity<MatchResponse> updateMatchStatus(
            @PathVariable Long id,
            @RequestBody MatchStatusRequest request
    ) {
        if (request.getStatus() == null) {
            return ResponseEntity.badRequest().build();
        }
        return sportMatchService.updateStatus(id, request.getStatus())
                .map(MatchResponse::from)
                .map(ResponseEntity::ok)
                .orElseGet(() -> ResponseEntity.notFound().build());
    }
}
