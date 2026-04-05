package com.naitik.backendapi.dto;

import lombok.Builder;
import lombok.Getter;

@Getter
@Builder
public class HighlightResponse {
    private Long id;
    private String clipFile;
    private String clipPath;
    private Double eventTimestamp;
    private String clock;
    private String oldScore;
    private String newScore;
    private Double clipStartTime;
    private Double duration;
}