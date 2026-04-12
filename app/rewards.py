from typing import Dict, Any
from app.models import Action, EnvState

def compute_reward(task: Dict[str, Any], state: EnvState, action: Action) -> Dict[str, Any]:
    gold = task["gold"]
    reward = 0.0
    components = {}

    if action.action_type == "inspect_policy":
        reward += 0.05
        components["inspect_policy"] = 0.05

    elif action.action_type == "tag_issue":
        delta = 0.20 if action.value == gold["tag"] else -0.05
        reward += delta
        components["tag_issue"] = delta

    elif action.action_type == "set_priority":
        delta = 0.15 if action.value == gold["priority"] else -0.05
        reward += delta
        components["set_priority"] = delta

    elif action.action_type == "assign_team":
        delta = 0.20 if action.value == gold["team"] else -0.10
        reward += delta
        components["assign_team"] = delta

    elif action.action_type == "ask_customer_question":
        text = (action.value or "").lower()
        if any(k in text for k in gold["must_ask"]):
            delta = 0.15
        else:
            delta = 0.02
        reward += delta
        components["ask_customer_question"] = delta

    elif action.action_type == "draft_reply":
        text = (action.value or "").lower()
        hits = sum(1 for k in gold["reply_keywords"] if k in text)
        delta = min(0.15, hits * 0.04)
        reward += delta
        components["draft_reply"] = delta

    elif action.action_type == "escalate":
        if gold["must_escalate"]:
            delta = 0.25
        else:
            delta = -0.05
        reward += delta
        components["escalate"] = delta

    elif action.action_type == "resolve_ticket":
        if gold["must_not_resolve_early"]:
            delta = -0.20
        else:
            delta = 0.10
        reward += delta
        components["resolve_ticket"] = delta

    if state.step_count > 6:
        reward -= 0.02
        components["long_episode_penalty"] = -0.02

    # Clamp reward to strict (0, 1) open interval for grader compliance
    reward = max(0.01, min(0.99, reward))

    return {
        "value": reward,
        "components": components,
        "explanation": "Shaped reward for incremental progress."
    }