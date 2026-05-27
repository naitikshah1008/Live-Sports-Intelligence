package com.naitik.backendapi.service;

import com.naitik.backendapi.dto.PipelineRunRequest;
import com.naitik.backendapi.dto.PipelineRunStatusRequest;
import com.naitik.backendapi.entity.PipelineRun;
import com.naitik.backendapi.entity.PipelineRunStatus;
import com.naitik.backendapi.entity.SportMatch;
import com.naitik.backendapi.repository.PipelineRunRepository;
import com.naitik.backendapi.repository.SportMatchRepository;
import org.springframework.stereotype.Service;

import java.time.Instant;
import java.util.List;
import java.util.Optional;

@Service
public class PipelineRunService {

    private final PipelineRunRepository pipelineRunRepository;
    private final SportMatchRepository sportMatchRepository;

    public PipelineRunService(
            PipelineRunRepository pipelineRunRepository,
            SportMatchRepository sportMatchRepository
    ) {
        this.pipelineRunRepository = pipelineRunRepository;
        this.sportMatchRepository = sportMatchRepository;
    }

    public PipelineRun createRun(PipelineRunRequest request) {
        PipelineRun run = new PipelineRun();
        run.setMatch(resolveMatch(request.getMatchId()));
        run.setMode(defaultIfBlank(request.getMode(), "offline"));
        run.setSourceType(request.getSourceType());
        run.setSourceUri(request.getSourceUri());
        run.setStatus(request.getStatus() != null ? request.getStatus() : PipelineRunStatus.QUEUED);
        applyStatusTimestamps(run, run.getStatus());
        return pipelineRunRepository.save(run);
    }

    public List<PipelineRun> getRuns(Long matchId) {
        if (matchId != null) {
            return pipelineRunRepository.findByMatch_IdOrderByCreatedAtDesc(matchId);
        }
        return pipelineRunRepository.findAllByOrderByCreatedAtDesc();
    }

    public Optional<PipelineRun> getRun(Long id) {
        return pipelineRunRepository.findById(id);
    }

    public Optional<PipelineRun> updateRun(Long id, PipelineRunStatusRequest request) {
        return pipelineRunRepository.findById(id)
                .map(run -> {
                    if (request.getStatus() != null) {
                        run.setStatus(request.getStatus());
                        applyStatusTimestamps(run, request.getStatus());
                    }
                    if (request.getFramesProcessed() != null) {
                        run.setFramesProcessed(request.getFramesProcessed());
                    }
                    if (request.getEventsDetected() != null) {
                        run.setEventsDetected(request.getEventsDetected());
                    }
                    if (request.getHighlightsGenerated() != null) {
                        run.setHighlightsGenerated(request.getHighlightsGenerated());
                    }
                    if (request.getErrorMessage() != null) {
                        run.setErrorMessage(request.getErrorMessage());
                    }
                    return pipelineRunRepository.save(run);
                });
    }

    private SportMatch resolveMatch(Long matchId) {
        if (matchId == null) {
            return null;
        }
        return sportMatchRepository.findById(matchId)
                .orElseThrow(() -> new IllegalArgumentException("Match not found: " + matchId));
    }

    private void applyStatusTimestamps(PipelineRun run, PipelineRunStatus status) {
        Instant now = Instant.now();
        if (status == PipelineRunStatus.RUNNING && run.getStartedAt() == null) {
            run.setStartedAt(now);
        }
        if (isTerminalStatus(status) && run.getFinishedAt() == null) {
            run.setFinishedAt(now);
        }
    }

    private boolean isTerminalStatus(PipelineRunStatus status) {
        return status == PipelineRunStatus.COMPLETED
                || status == PipelineRunStatus.FAILED
                || status == PipelineRunStatus.CANCELED;
    }

    private String defaultIfBlank(String value, String fallback) {
        return value == null || value.isBlank() ? fallback : value;
    }
}
