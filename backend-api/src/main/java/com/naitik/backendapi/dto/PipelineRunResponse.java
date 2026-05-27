package com.naitik.backendapi.dto;

import com.naitik.backendapi.entity.PipelineRun;
import com.naitik.backendapi.entity.PipelineRunStatus;
import com.naitik.backendapi.entity.SportMatch;
import lombok.Builder;
import lombok.Getter;

import java.time.Instant;

@Getter
@Builder
public class PipelineRunResponse {
    private Long id;
    private Long matchId;
    private String matchName;
    private String mode;
    private String sourceType;
    private String sourceUri;
    private PipelineRunStatus status;
    private Long framesProcessed;
    private Long eventsDetected;
    private Long highlightsGenerated;
    private String errorMessage;
    private Instant startedAt;
    private Instant finishedAt;
    private Instant createdAt;
    private Instant updatedAt;

    public static PipelineRunResponse from(PipelineRun run) {
        SportMatch match = run.getMatch();
        return PipelineRunResponse.builder()
                .id(run.getId())
                .matchId(match != null ? match.getId() : null)
                .matchName(match != null ? match.getName() : null)
                .mode(run.getMode())
                .sourceType(run.getSourceType())
                .sourceUri(run.getSourceUri())
                .status(run.getStatus())
                .framesProcessed(run.getFramesProcessed())
                .eventsDetected(run.getEventsDetected())
                .highlightsGenerated(run.getHighlightsGenerated())
                .errorMessage(run.getErrorMessage())
                .startedAt(run.getStartedAt())
                .finishedAt(run.getFinishedAt())
                .createdAt(run.getCreatedAt())
                .updatedAt(run.getUpdatedAt())
                .build();
    }
}
