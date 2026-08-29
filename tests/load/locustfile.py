#!/usr/bin/env python3
"""
V41.0 — Load Testing with Locust.
"""

from locust import HttpUser, task, between

class AerynUser(HttpUser):
    wait_time = between(1, 3)
    
    @task(3)
    def health_check(self):
        self.client.get("/health")
    
    @task(2)
    def chat(self):
        self.client.post("/chat", json={"goal": "Hello Aeryn, how are you?"})
    
    @task(1)
    def search(self):
        self.client.get("/search?q=test&limit=5")
    
    @task(1)
    def vault_entries(self):
        self.client.get("/vault/entries")
