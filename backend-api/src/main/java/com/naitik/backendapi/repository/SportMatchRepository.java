package com.naitik.backendapi.repository;

import com.naitik.backendapi.entity.SportMatch;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;

public interface SportMatchRepository extends JpaRepository<SportMatch, Long> {
    List<SportMatch> findAllByOrderByCreatedAtDesc();
}
