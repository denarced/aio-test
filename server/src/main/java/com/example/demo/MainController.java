package com.example.demo;

import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RestController;

@RestController
public class MainController {
    @PostMapping("/process")
    public String hello(@RequestBody String content) throws InterruptedException {
        Thread.sleep(400L);
        return String.valueOf(content.length());
    }
}
