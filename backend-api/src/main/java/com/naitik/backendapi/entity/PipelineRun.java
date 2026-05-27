package com.naitik.backendapi.entity;

import jakarta.persistence.*;
import lombok.Getter;
import lombok.Setter;

import java.time.Instant;

@Entity
@Table(name = "pipeline_runs")
@Getter
@Setter
public class PipelineRun {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @ManyToOne(fetch = FetchType.EAGER)
    @JoinColumn(name = "match_id")
    private SportMatch match;

    @Column(nullable = false)
    private String mode;

    @Column(name = "source_type")
    private String sourceType;

    @Column(name = "source_uri", length = 1000)
    private String sourceUri;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false)
    private PipelineRunStatus status;

    @Column(name = "frames_processed", nullable = false)
    private Long framesProcessed;

    @Column(name = "events_detected", nullable = false)
    private Long eventsDetected;

    @Column(name = "highlights_generated", nullable = false)
    private Long highlightsGenerated;

    @Column(name = "error_message", length = 2000)
    private String errorMessage;

    @Column(name = "started_at")
    private Instant startedAt;

    @Column(name = "finished_at")
    private Instant finishedAt;

    @Column(name = "created_at", nullable = false)
    private Instant createdAt;

    @Column(name = "updated_at", nullable = false)
    private Instant updatedAt;

    @PrePersist
    void onCreate() {
        Instant now = Instant.now();
        if (status == null) {
            status = PipelineRunStatus.QUEUED;
        }
        if (framesProcessed == null) {
            framesProcessed = 0L;
        }
        if (eventsDetected == null) {
            eventsDetected = 0L;
        }
        if (highlightsGenerated == null) {
            highlightsGenerated = 0L;
        }
        createdAt = now;
        updatedAt = now;
    }

    @PreUpdate
    void onUpdate() {
        updatedAt = Instant.now();
    }
}
