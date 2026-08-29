#!/usr/bin/env python3
"""
V41.0 — Aeryn SDK Python.
Official Python SDK for Aeryn API.
"""

import os
import json
import urllib.request
import urllib.error
from typing import Dict, List, Optional, Any


class AerynClient:
    """Aeryn API Client."""
    
    def __init__(self, api_key: str = None, base_url: str = "http://127.0.0.1:3010"):
        self.api_key = api_key or os.environ.get("AERYN_API_KEY", "")
        self.base_url = base_url.rstrip("/")
        self._token = None
    
    def _request(self, method: str, path: str, data: Dict = None) -> Dict:
        """Make API request."""
        url = f"{self.base_url}{path}"
        
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        elif self._token:
            headers["Authorization"] = f"Bearer {self._token}"
        
        body = json.dumps(data).encode() if data else None
        req = urllib.request.Request(url, data=body, headers=headers, method=method)
        
        try:
            response = urllib.request.urlopen(req, timeout=30)
            return json.loads(response.read().decode())
        except urllib.error.HTTPError as e:
            error_body = e.read().decode()
            try:
                return json.loads(error_body)
            except:
                return {"error": error_body}
    
    # ── Auth ─────────────────────────────────────
    
    def register(self, email: str, password: str, display_name: str = None) -> Dict:
        """Register a new user."""
        return self._request("POST", "/auth/register", {
            "email": email,
            "password": password,
            "display_name": display_name,
        })
    
    def login(self, email: str, password: str) -> Dict:
        """Login and get token."""
        result = self._request("POST", "/auth/login", {
            "email": email,
            "password": password,
        })
        if "token" in result:
            self._token = result["token"]
        return result
    
    def validate_token(self, token: str = None) -> Dict:
        """Validate a token."""
        return self._request("POST", "/auth/validate", {
            "token": token or self._token,
        })
    
    def forgot_password(self, email: str) -> Dict:
        """Request password reset."""
        return self._request("POST", "/auth/forgot-password", {"email": email})
    
    def reset_password(self, token: str, new_password: str) -> Dict:
        """Reset password."""
        return self._request("POST", "/auth/reset-password", {
            "token": token,
            "new_password": new_password,
        })
    
    def create_api_key(self, name: str = "default", scopes: List[str] = None) -> Dict:
        """Create an API key."""
        return self._request("POST", "/auth/api-keys", {
            "name": name,
            "scopes": scopes,
        })
    
    # ── Chat ─────────────────────────────────────
    
    def chat(self, message: str, session_id: str = None) -> Dict:
        """Send a chat message."""
        return self._request("POST", "/chat", {
            "goal": message,
            "session_id": session_id,
        })
    
    # ── Search ───────────────────────────────────
    
    def search(self, query: str, limit: int = 10) -> Dict:
        """Search memories."""
        return self._request("GET", f"/search?q={query}&limit={limit}")
    
    # ── Tasks ────────────────────────────────────
    
    def list_tasks(self) -> Dict:
        """List all tasks."""
        return self._request("GET", "/shared/tasks/all")
    
    def create_task(self, title: str, description: str = None, priority: str = "normal") -> Dict:
        """Create a task."""
        return self._request("POST", "/shared/tasks/add", {
            "title": title,
            "description": description,
            "priority": priority,
        })
    
    # ─ Notifications ───────────────────────────
    
    def list_notifications(self) -> Dict:
        """List pending notifications."""
        return self._request("GET", "/notifications/pending")
    
    def create_notification(self, title: str, message: str, priority: str = "normal") -> Dict:
        """Create a notification."""
        return self._request("POST", "/notifications/create", {
            "title": title,
            "message": message,
            "priority": priority,
        })
    
    # ── Vault ───────────────────────────────────
    
    def list_vault_entries(self) -> Dict:
        """List vault entries."""
        return self._request("GET", "/vault/entries")
    
    def search_vault(self, query: str) -> Dict:
        """Search vault."""
        return self._request("GET", f"/vault/search?q={query}")
    
    # ── Billing ─────────────────────────────────
    
    def get_usage(self, days: int = 30) -> Dict:
        """Get usage summary."""
        return self._request("GET", f"/usage/summary?days={days}")
    
    def get_quota(self) -> Dict:
        """Check quota."""
        return self._request("GET", "/billing/quota")
    
    def get_pricing(self) -> Dict:
        """Get pricing info."""
        return self._request("GET", "/billing/pricing")
    
    # ── Webhooks ───────────────────────────────
    
    def register_webhook(self, url: str, events: List[str] = None) -> Dict:
        """Register a webhook."""
        return self._request("POST", "/webhooks/register", {
            "url": url,
            "events": events,
        })
    
    def list_webhooks(self) -> Dict:
        """List webhooks."""
        return self._request("GET", "/webhooks")
    
    def unregister_webhook(self, webhook_id: str) -> Dict:
        """Unregister a webhook."""
        return self._request("DELETE", f"/webhooks/unregister?webhook_id={webhook_id}")
    
    # ── Plugins ────────────────────────────────
    
    def list_plugins(self, query: str = None, limit: int = 20) -> Dict:
        """List public plugins."""
        path = f"/plugins?limit={limit}"
        if query:
            path += f"&query={query}"
        return self._request("GET", path)
    
    def publish_plugin(self, name: str, source_code: str, **kwargs) -> Dict:
        """Publish a plugin."""
        data = {"name": name, "source_code": source_code}
        data.update(kwargs)
        return self._request("POST", "/plugins/publish", data)
    
    def get_plugin(self, plugin_id: str) -> Dict:
        """Get plugin details."""
        return self._request("GET", f"/plugins/{plugin_id}")
    
    def rate_plugin(self, plugin_id: str, rating: float) -> Dict:
        """Rate a plugin."""
        return self._request("POST", "/plugins/rate", {
            "plugin_id": plugin_id,
            "rating": rating,
        })
    
    # ── Proactive ──────────────────────────────
    
    def get_suggestions(self) -> Dict:
        """Get proactive suggestions."""
        return self._request("GET", "/proactive/suggestions")
    
    def get_patterns(self) -> Dict:
        """Get usage patterns."""
        return self._request("GET", "/proactive/v2/patterns")
    
    def get_anomalies(self) -> Dict:
        """Get anomalies."""
        return self._request("GET", "/proactive/v2/anomalies")
    
    def morning_briefing(self) -> Dict:
        """Generate morning briefing."""
        return self._request("POST", "/briefing/morning")
    
    def evening_briefing(self) -> Dict:
        """Generate evening briefing."""
        return self._request("POST", "/briefing/evening")


# ── Convenience Functions ─────────────────────

def create_client(api_key: str = None, base_url: str = "http://127.0.0.1:3010") -> AerynClient:
    """Create an Aeryn client."""
    return AerynClient(api_key=api_key, base_url=base_url)
