package com.naitik.backendapi.dto;

import com.naitik.backendapi.entity.MatchStatus;
import lombok.Getter;
import lombok.Setter;

@Getter
@Setter
public class MatchStatusRequest {
    private MatchStatus status;
}
