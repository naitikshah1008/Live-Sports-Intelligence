package com.naitik.backendapi.dto;

import lombok.Builder;
import lombok.Getter;

@Getter
@Builder
public class DashboardSummaryResponse {
    private String latestClock;
    private String latestScore;
    private String latestEvent;
    private long totalEvents;
    private long totalHighlights;
}