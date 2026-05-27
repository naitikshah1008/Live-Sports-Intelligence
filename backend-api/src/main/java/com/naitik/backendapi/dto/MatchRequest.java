package com.naitik.backendapi.dto;

import com.naitik.backendapi.entity.MatchStatus;
import lombok.Getter;
import lombok.Setter;

import java.time.Instant;

@Getter
@Setter
public class MatchRequest {
    private String name;
    private String sport;
    private String homeTeam;
    private String awayTeam;
    private String venue;
    private Instant scheduledStartTime;
    private MatchStatus status;
}
