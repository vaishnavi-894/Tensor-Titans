from typing import Dict, Any
from app.models import EnvState

def contains_any(texts, keywords):
    joined = " ".join(texts).lower()
    return any(k.lower() in joined for k in keywords)

def grade_task(task: Dict[str, Any], state: EnvState) -> Dict[str, Any]:
    gold = task["gold"]
    score = 0.0
    breakdown = {}

    tag_score = 1.0 if state.tag == gold["tag"] else 0.0
    breakdown["tag"] = 0.20 * tag_score
    score += breakdown["tag"]

    priority_score = 1.0 if state.priority == gold["priority"] else 0.0
    breakdown["priority"] = 0.20 * priority_score
    score += breakdown["priority"]

    team_score = 1.0 if state.assigned_team == gold["team"] else 0.0
    breakdown["team"] = 0.20 * team_score
    score += breakdown["team"]

    must_ask_score = 1.0 if contains_any(state.questions_asked, gold["must_ask"]) else 0.0
    breakdown["must_ask"] = 0.15 * must_ask_score
    score += breakdown["must_ask"]

    reply_score = 1.0 if contains_any(state.drafted_replies, gold["reply_keywords"]) else 0.0
    breakdown["reply_quality"] = 0.15 * reply_score
    score += breakdown["reply_quality"]

    if gold["must_escalate"]:
        escalation_score = 1.0 if state.escalated else 0.0
    else:
        escalation_score = 1.0 if not state.escalated else 0.5

    breakdown["escalation"] = 0.10 * escalation_score
    score += breakdown["escalation"]

    score = max(0.01, min(0.99, score))
    
    return {
        "score": score,
        "breakdown": breakdown,
        "passed": score >= 0.75
    }