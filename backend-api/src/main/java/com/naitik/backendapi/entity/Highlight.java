package com.naitik.backendapi.entity;

import jakarta.persistence.*;
import lombok.Getter;
import lombok.Setter;

import java.time.Instant;

@Entity
@Table(name = "highlights")
@Getter
@Setter
public class Highlight {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "clip_file", nullable = false, unique = true)
    private String clipFile;

    @Column(name = "clip_path", nullable = false, length = 1000)
    private String clipPath;

    @Column(name = "event_timestamp", nullable = false)
    private Double eventTimestamp;

    @Column(nullable = false)
    private String clock;

    @Column(name = "old_score", nullable = false)
    private String oldScore;

    @Column(name = "new_score", nullable = false)
    private String newScore;

    @Column(name = "clip_start_time", nullable = false)
    private Double clipStartTime;

    @Column(nullable = false)
    private Double duration;

    @Column(name = "created_at", nullable = false)
    private Instant createdAt;
}