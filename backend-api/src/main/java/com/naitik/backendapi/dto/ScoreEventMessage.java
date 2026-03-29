package com.naitik.backendapi.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.Getter;
import lombok.Setter;

@Getter
@Setter
public class ScoreEventMessage {

    @JsonProperty("event_type")
    private String eventType;

    private Double timestamp;
    private String clock;

    @JsonProperty("old_score")
    private String oldScore;

    @JsonProperty("new_score")
    private String newScore;

    private String file;
}