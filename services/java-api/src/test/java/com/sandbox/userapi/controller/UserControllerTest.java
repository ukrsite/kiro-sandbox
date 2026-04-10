package com.sandbox.userapi.controller;

import com.sandbox.userapi.model.User;
import com.sandbox.userapi.repository.UserRepository;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.web.servlet.MockMvc;

import static org.assertj.core.api.Assertions.assertThat;

@SpringBootTest
@AutoConfigureMockMvc
class UserControllerTest {

    @Autowired
    private MockMvc mockMvc;

    @Autowired
    private UserRepository userRepository;

    @BeforeEach
    void setUp() {
        userRepository.deleteAll();

        User admin = new User();
        admin.setName("Admin");
        admin.setEmail("admin@example.com");
        admin.setRole("ADMIN");
        admin.setActive(true);
        userRepository.save(admin);

        User user = new User();
        user.setName("Regular User");
        user.setEmail("user@example.com");
        user.setRole("USER");
        user.setActive(true);
        userRepository.save(user);
    }

    @Test
    void contextLoads() {
        assertThat(mockMvc).isNotNull();
    }
}
