package com.sandbox.userapi.dto;

import jakarta.validation.constraints.NotNull;

public record UpdateUserRequest(@NotNull Boolean active) {}
