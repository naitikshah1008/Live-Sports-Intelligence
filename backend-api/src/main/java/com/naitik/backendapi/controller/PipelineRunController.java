package com.naitik.backendapi.controller;

import com.naitik.backendapi.dto.PipelineRunRequest;
import com.naitik.backendapi.dto.PipelineRunResponse;
import com.naitik.backendapi.dto.PipelineRunStatusRequest;
import com.naitik.backendapi.entity.PipelineRun;
import com.naitik.backendapi.service.PipelineRunService;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/pipeline-runs")
@RequiredArgsConstructor
@CrossOrigin(origins = "*")
public class PipelineRunController {

    private final PipelineRunService pipelineRunService;

    @PostMapping
    public ResponseEntity<PipelineRunResponse> createPipelineRun(@RequestBody PipelineRunRequest request) {
        try {
            PipelineRun run = pipelineRunService.createRun(request);
            return ResponseEntity.status(HttpStatus.CREATED).body(PipelineRunResponse.from(run));
        } catch (IllegalArgumentException error) {
            return ResponseEntity.badRequest().build();
        }
    }

    @GetMapping
    public List<PipelineRunResponse> getPipelineRuns(@RequestParam(required = false) Long matchId) {
        return pipelineRunService.getRuns(matchId).stream()
                .map(PipelineRunResponse::from)
                .toList();
    }

    @GetMapping("/{id}")
    public ResponseEntity<PipelineRunResponse> getPipelineRun(@PathVariable Long id) {
        return pipelineRunService.getRun(id)
                .map(PipelineRunResponse::from)
                .map(ResponseEntity::ok)
                .orElseGet(() -> ResponseEntity.notFound().build());
    }

    @PatchMapping("/{id}")
    public ResponseEntity<PipelineRunResponse> updatePipelineRun(
            @PathVariable Long id,
            @RequestBody PipelineRunStatusRequest request
    ) {
        return pipelineRunService.updateRun(id, request)
                .map(PipelineRunResponse::from)
                .map(ResponseEntity::ok)
                .orElseGet(() -> ResponseEntity.notFound().build());
    }
}
