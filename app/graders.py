from typing import Dict, Any
from app.models import EnvState

def _clamp(v: float) -> float:
    """Clamp a value to strict (0, 1) open interval."""
    return max(0.01, min(0.99, v))

def contains_any(texts, keywords):
    joined = " ".join(texts).lower()
    return any(k.lower() in joined for k in keywords)

def grade_task(task: Dict[str, Any], state: EnvState) -> Dict[str, Any]:
    gold = task["gold"]
    score = 0.0
    breakdown = {}

    tag_score = 1.0 if state.tag == gold["tag"] else 0.0
    breakdown["tag"] = _clamp(0.20 * tag_score)
    score += 0.20 * tag_score

    priority_score = 1.0 if state.priority == gold["priority"] else 0.0
    breakdown["priority"] = _clamp(0.20 * priority_score)
    score += 0.20 * priority_score

    team_score = 1.0 if state.assigned_team == gold["team"] else 0.0
    breakdown["team"] = _clamp(0.20 * team_score)
    score += 0.20 * team_score

    must_ask_score = 1.0 if contains_any(state.questions_asked, gold["must_ask"]) else 0.0
    breakdown["must_ask"] = _clamp(0.15 * must_ask_score)
    score += 0.15 * must_ask_score

    reply_score = 1.0 if contains_any(state.drafted_replies, gold["reply_keywords"]) else 0.0
    breakdown["reply_quality"] = _clamp(0.15 * reply_score)
    score += 0.15 * reply_score

    if gold["must_escalate"]:
        escalation_score = 1.0 if state.escalated else 0.0
    else:
        escalation_score = 1.0 if not state.escalated else 0.5

    breakdown["escalation"] = _clamp(0.10 * escalation_score)
    score += 0.10 * escalation_score

    score = _clamp(score)
    
    return {
        "score": score,
        "breakdown": breakdown,
        "passed": score >= 0.75
    }