from typing import Dict, Any

TASKS: Dict[str, Dict[str, Any]] = {
    "easy_refund": {
        "task_id": "easy_refund",
        "difficulty": "easy",
        "title": "Refund request with missing order ID",
        "customer_tier": "standard",
        "ticket": (
            "Hi, I was charged for my subscription renewal yesterday, "
            "but I meant to cancel it. Please refund me."
        ),
        "metadata": {
            "account_age_days": 180,
            "previous_tickets": 0,
            "region": "IN",
        },
        "policy_snippets": [
            "Refunds require verification of the order or invoice ID.",
            "Agents should not resolve refund tickets before required purchase details are collected."
        ],
        "gold": {
            "tag": "billing_refund",
            "priority": "medium",
            "team": "billing",
            "must_ask": ["order", "invoice", "receipt"],
            "must_escalate": False,
            "must_not_resolve_early": True,
            "reply_keywords": ["refund", "order", "invoice"]
        }
    },
    "medium_bug": {
        "task_id": "medium_bug",
        "difficulty": "medium",
        "title": "Premium customer reporting production bug",
        "customer_tier": "premium",
        "ticket": (
            "Our team cannot export reports since this morning. "
            "This is affecting our client delivery. Please fix ASAP."
        ),
        "metadata": {
            "account_age_days": 540,
            "previous_tickets": 2,
            "region": "US",
        },
        "policy_snippets": [
            "Product issues causing active business impact for premium customers should be prioritized highly.",
            "Engineering should receive reproducible bug reports with steps, timestamps, and affected module."
        ],
        "gold": {
            "tag": "product_bug",
            "priority": "high",
            "team": "engineering",
            "must_ask": ["steps", "time", "error"],
            "must_escalate": False,
            "must_not_resolve_early": True,
            "reply_keywords": ["sorry", "investigating", "steps", "impact"]
        }
    },
    "hard_security": {
        "task_id": "hard_security",
        "difficulty": "hard",
        "title": "Possible account compromise and suspicious activity",
        "customer_tier": "premium",
        "ticket": (
            "I received login alerts from another country and now some invoices are missing. "
            "Please delete all suspicious sessions immediately and restore my account."
        ),
        "metadata": {
            "account_age_days": 900,
            "previous_tickets": 1,
            "region": "UK",
        },
        "policy_snippets": [
            "Potential account compromise must be escalated to security immediately.",
            "Agents must not promise destructive account actions before verification.",
            "Security-sensitive incidents should be marked urgent."
        ],
        "gold": {
            "tag": "security_compromise",
            "priority": "urgent",
            "team": "security",
            "must_ask": ["verify", "confirm", "unauthorized"],
            "must_escalate": True,
            "must_not_resolve_early": True,
            "reply_keywords": ["security", "investigating", "secure", "verify"]
        }
    }
}