package com.naitik.backendapi.service;

import com.naitik.backendapi.dto.MatchRequest;
import com.naitik.backendapi.entity.MatchStatus;
import com.naitik.backendapi.entity.SportMatch;
import com.naitik.backendapi.repository.SportMatchRepository;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.Optional;

@Service
public class SportMatchService {

    private final SportMatchRepository sportMatchRepository;

    public SportMatchService(SportMatchRepository sportMatchRepository) {
        this.sportMatchRepository = sportMatchRepository;
    }

    public SportMatch createMatch(MatchRequest request) {
        SportMatch match = new SportMatch();
        match.setName(defaultIfBlank(request.getName(), "Untitled match"));
        match.setSport(defaultIfBlank(request.getSport(), "soccer"));
        match.setHomeTeam(request.getHomeTeam());
        match.setAwayTeam(request.getAwayTeam());
        match.setVenue(request.getVenue());
        match.setScheduledStartTime(request.getScheduledStartTime());
        match.setStatus(request.getStatus() != null ? request.getStatus() : MatchStatus.PLANNED);
        return sportMatchRepository.save(match);
    }

    public List<SportMatch> getMatches() {
        return sportMatchRepository.findAllByOrderByCreatedAtDesc();
    }

    public Optional<SportMatch> getMatch(Long id) {
        return sportMatchRepository.findById(id);
    }

    public Optional<SportMatch> updateStatus(Long id, MatchStatus status) {
        if (status == null) {
            return Optional.empty();
        }
        return sportMatchRepository.findById(id)
                .map(match -> {
                    match.setStatus(status);
                    return sportMatchRepository.save(match);
                });
    }

    private String defaultIfBlank(String value, String fallback) {
        return value == null || value.isBlank() ? fallback : value;
    }
}
