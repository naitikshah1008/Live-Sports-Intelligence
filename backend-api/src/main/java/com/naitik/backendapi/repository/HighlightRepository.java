package com.naitik.backendapi.repository;

import com.naitik.backendapi.entity.Highlight;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;
import java.util.Optional;

public interface HighlightRepository extends JpaRepository<Highlight, Long> {
    List<Highlight> findAllByOrderByEventTimestampAsc();
    List<Highlight> findTop10ByOrderByCreatedAtDesc();
    Optional<Highlight> findByClipFile(String clipFile);
}