package com.sandbox.userapi.service;

import com.sandbox.userapi.model.User;
import com.sandbox.userapi.repository.UserRepository;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import static org.assertj.core.api.Assertions.assertThat;

@ExtendWith(MockitoExtension.class)
class UserServiceTest {

    @Mock
    private UserRepository userRepository;

    @InjectMocks
    private UserService userService;

    private User activeUser;

    @BeforeEach
    void setUp() {
        activeUser = new User();
        activeUser.setId(10L);
        activeUser.setName("John Doe");
        activeUser.setEmail("john@example.com");
        activeUser.setRole("USER");
        activeUser.setActive(true);
    }

    @Test
    void contextLoads() {
        assertThat(userService).isNotNull();
    }
}
