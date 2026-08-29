#!/usr/bin/env python3
"""
V41.0 — Phase 3: Stripe Billing.
Usage-based billing with Stripe integration.
"""

import os
import json
import uuid
import hashlib
import hmac
from typing import Dict, List, Optional
from datetime import datetime, timedelta

from aeryn_core.neon_db import get_neon
from aeryn_core.logger import info, warn, error

# Pricing (usage-based)
PRICING = {
    "chat:input": 0.001,      # $0.001 per 1K input tokens
    "chat:output": 0.002,     # $0.002 per 1K output tokens
    "search": 0.0005,         # $0.0005 per search
    "notification": 0.0001,   # $0.0001 per notification
}

# Plans
PLANS = {
    "free": {
        "name": "Free",
        "price": 0,
        "quota": {"tokens": 10000, "requests": 1000},
        "features": ["basic_chat", "basic_search"],
    },
    "pro": {
        "name": "Pro",
        "price": 29,
        "quota": {"tokens": 1000000, "requests": 100000},
        "features": ["basic_chat", "advanced_search", "priority_support"],
    },
    "enterprise": {
        "name": "Enterprise",
        "price": None,  # Custom
        "quota": {"tokens": None, "requests": None},  # Unlimited
        "features": ["all_features"],
    },
}


class BillingManager:
    """Manage billing and subscriptions."""
    
    def __init__(self):
        self.db = get_neon()
        self.stripe_key = os.environ.get("STRIPE_SECRET_KEY", "")
        self.stripe_webhook_secret = os.environ.get("STRIPE_WEBHOOK_SECRET", "")
    
    def track_charge(self, user_id: str, amount: float, description: str = "",
                     metadata: dict = None) -> Dict:
        """Record a charge."""
        charge_id = f"ch_{uuid.uuid4().hex[:12]}"
        
        self.db.insert('usage_events', {
            'id': charge_id,
            'user_id': user_id,
            'event_type': 'charge',
            'endpoint': '',
            'tokens_input': 0,
            'tokens_output': 0,
            'cost': amount,
            'metadata': json.dumps(metadata or {"description": description}),
        })
        
        return {"charge_id": charge_id, "amount": amount}
    
    def calculate_cost(self, event_type: str, tokens_input: int = 0,
                       tokens_output: int = 0, count: int = 1) -> float:
        """Calculate cost for an event."""
        if event_type == "chat":
            input_cost = (tokens_input / 1000) * PRICING["chat:input"]
            output_cost = (tokens_output / 1000) * PRICING["chat:output"]
            return round(input_cost + output_cost, 6)
        elif event_type == "search":
            return round(count * PRICING["search"], 6)
        elif event_type == "notification":
            return round(count * PRICING["notification"], 6)
        return 0.0
    
    def check_quota(self, user_id: str, plan: str = "free") -> Dict:
        """Check if user has exceeded their quota."""
        plan_config = PLANS.get(plan, PLANS["free"])
        quota = plan_config["quota"]
        
        # Get current usage (this month)
        now = datetime.now()
        start_of_month = now.replace(day=1, hour=0, minute=0, second=0)
        
        usage = self.db.fetchone("""
            SELECT SUM(tokens_input + tokens_output) as total_tokens,
                   COUNT(*) as total_requests
            FROM usage_events
            WHERE user_id = %s AND created_at >= %s
        """, (user_id, start_of_month))
        
        current_tokens = usage.get("total_tokens", 0) or 0
        current_requests = usage.get("total_requests", 0) or 0
        
        tokens_remaining = (quota["tokens"] - current_tokens) if quota["tokens"] else None
        requests_remaining = (quota["requests"] - current_requests) if quota["requests"] else None
        
        return {
            "plan": plan,
            "tokens_used": current_tokens,
            "tokens_limit": quota["tokens"],
            "tokens_remaining": tokens_remaining,
            "requests_used": current_requests,
            "requests_limit": quota["requests"],
            "requests_remaining": requests_remaining,
            "within_quota": (
                (tokens_remaining is None or tokens_remaining > 0) and
                (requests_remaining is None or requests_remaining > 0)
            ),
        }
    
    def create_stripe_customer(self, email: str, name: str = None) -> Optional[Dict]:
        """Create a Stripe customer (placeholder for actual Stripe integration)."""
        if not self.stripe_key:
            warn("Stripe key not configured")
            return None
        
        # TODO: Implement actual Stripe API call
        # customer = stripe.Customer.create(email=email, name=name)
        return {"id": f"cus_{uuid.uuid4().hex[:12]}", "email": email}
    
    def create_subscription(self, customer_id: str, plan: str = "pro") -> Optional[Dict]:
        """Create a subscription (placeholder)."""
        if not self.stripe_key:
            warn("Stripe key not configured")
            return None
        
        # TODO: Implement actual Stripe subscription
        return {
            "id": f"sub_{uuid.uuid4().hex[:12]}",
            "customer": customer_id,
            "plan": plan,
            "status": "active",
        }
    
    def process_webhook(self, payload: bytes, signature: str) -> Optional[Dict]:
        """Process a Stripe webhook."""
        if not self.stripe_key or not self.stripe_webhook_secret:
            return None
        
        # TODO: Verify webhook signature and process event
        # event = stripe.Webhook.construct_event(payload, signature, self.stripe_webhook_secret)
        return None


# ── Singleton ─────────────────────────────────

_billing: Optional[BillingManager] = None

def get_billing() -> BillingManager:
    global _billing
    if _billing is None:
        _billing = BillingManager()
    return _billing
