package com.naitik.backendapi.dto;

import com.naitik.backendapi.entity.PipelineRunStatus;
import lombok.Getter;
import lombok.Setter;

@Getter
@Setter
public class PipelineRunRequest {
    private Long matchId;
    private String mode;
    private String sourceType;
    private String sourceUri;
    private PipelineRunStatus status;
}
