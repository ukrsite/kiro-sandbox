package com.sandbox.userapi.dto;

import com.sandbox.userapi.model.User;

public record UserResponse(Long id, String name, String email, String role, boolean active) {
    public static UserResponse from(User user) {
        return new UserResponse(user.getId(), user.getName(), user.getEmail(), user.getRole(), user.isActive());
    }
}
