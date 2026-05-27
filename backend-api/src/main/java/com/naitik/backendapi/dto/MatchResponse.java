package com.naitik.backendapi.dto;

import com.naitik.backendapi.entity.MatchStatus;
import com.naitik.backendapi.entity.SportMatch;
import lombok.Builder;
import lombok.Getter;

import java.time.Instant;

@Getter
@Builder
public class MatchResponse {
    private Long id;
    private String name;
    private String sport;
    private String homeTeam;
    private String awayTeam;
    private String venue;
    private Instant scheduledStartTime;
    private MatchStatus status;
    private Instant createdAt;
    private Instant updatedAt;

    public static MatchResponse from(SportMatch match) {
        return MatchResponse.builder()
                .id(match.getId())
                .name(match.getName())
                .sport(match.getSport())
                .homeTeam(match.getHomeTeam())
                .awayTeam(match.getAwayTeam())
                .venue(match.getVenue())
                .scheduledStartTime(match.getScheduledStartTime())
                .status(match.getStatus())
                .createdAt(match.getCreatedAt())
                .updatedAt(match.getUpdatedAt())
                .build();
    }
}
