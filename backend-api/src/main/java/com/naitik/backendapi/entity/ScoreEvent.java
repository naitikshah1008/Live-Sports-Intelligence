package com.naitik.backendapi.entity;

import jakarta.persistence.*;
import lombok.Getter;
import lombok.Setter;

import java.time.Instant;

@Entity
@Table(name = "score_events")
@Getter
@Setter
public class ScoreEvent {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "event_type", nullable = false)
    private String eventType;

    @Column(name = "video_timestamp", nullable = false)
    private Double videoTimestamp;

    @Column(nullable = false)
    private String clock;

    @Column(name = "old_score", nullable = false)
    private String oldScore;

    @Column(name = "new_score", nullable = false)
    private String newScore;

    @Column(nullable = false)
    private String file;

    @Column(name = "created_at", nullable = false)
    private Instant createdAt;
}