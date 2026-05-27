package com.naitik.backendapi.repository;

import com.naitik.backendapi.entity.PipelineRun;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;

public interface PipelineRunRepository extends JpaRepository<PipelineRun, Long> {
    List<PipelineRun> findAllByOrderByCreatedAtDesc();
    List<PipelineRun> findByMatch_IdOrderByCreatedAtDesc(Long matchId);
}
