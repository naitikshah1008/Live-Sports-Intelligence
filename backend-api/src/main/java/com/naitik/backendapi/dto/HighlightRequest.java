package com.naitik.backendapi.dto;

import lombok.Getter;
import lombok.Setter;

@Getter
@Setter
public class HighlightRequest {
    private String clipFile;
    private String clipPath;
    private Double eventTimestamp;
    private String clock;
    private String oldScore;
    private String newScore;
    private Double startTime;
    private Double duration;
}