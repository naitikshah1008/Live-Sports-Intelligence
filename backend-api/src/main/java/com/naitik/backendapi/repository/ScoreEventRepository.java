package com.naitik.backendapi.repository;

import com.naitik.backendapi.entity.ScoreEvent;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;
import java.util.Optional;

public interface ScoreEventRepository extends JpaRepository<ScoreEvent, Long> {
    List<ScoreEvent> findAllByOrderByVideoTimestampAsc();
    List<ScoreEvent> findTop10ByOrderByCreatedAtDesc();
    List<ScoreEvent> findAllByOrderByCreatedAtDesc();
    Optional<ScoreEvent> findTopByOrderByCreatedAtDesc();
    List<ScoreEvent> findByClockAndOldScoreAndNewScore(String clock, String oldScore, String newScore);
}