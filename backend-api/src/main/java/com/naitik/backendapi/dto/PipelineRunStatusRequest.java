package com.naitik.backendapi.dto;

import com.naitik.backendapi.entity.PipelineRunStatus;
import lombok.Getter;
import lombok.Setter;

@Getter
@Setter
public class PipelineRunStatusRequest {
    private PipelineRunStatus status;
    private Long framesProcessed;
    private Long eventsDetected;
    private Long highlightsGenerated;
    private String errorMessage;
}
