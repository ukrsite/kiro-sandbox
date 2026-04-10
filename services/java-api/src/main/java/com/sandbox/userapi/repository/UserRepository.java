package com.sandbox.userapi.repository;

import com.sandbox.userapi.model.User;
import org.springframework.data.jpa.repository.JpaRepository;

public interface UserRepository extends JpaRepository<User, Long> {
}
