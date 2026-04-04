import os
import json
import re
from openai import OpenAI
import requests

API_BASE_URL = os.getenv("API_BASE_URL", "https://router.huggingface.co/v1")
HF_TOKEN = os.getenv("HF_TOKEN") or os.getenv("API_KEY")
MODEL_NAME = os.getenv("MODEL_NAME")
ENV_BASE_URL = os.getenv("ENV_BASE_URL", "http://127.0.0.1:8000")

MAX_STEPS = 8
TEMPERATURE = 0.0  # more deterministic
TASK_IDS = ["easy_refund", "medium_bug", "hard_security"]

SYSTEM_PROMPT = """
You are an AI agent operating a customer support ticket triage environment.

You must choose EXACTLY ONE action per step.

You MUST respond ONLY with valid JSON.
No explanation. No extra text. No markdown.

Valid format:
{"action_type":"tag_issue","value":"billing_refund"}

Allowed action_type values:
- inspect_policy
- tag_issue
- set_priority
- assign_team
- ask_customer_question
- draft_reply
- escalate
- resolve_ticket

Allowed tag_issue values:
- billing_refund
- product_bug
- security_compromise

Allowed set_priority values:
- medium
- high
- urgent

Allowed assign_team values:
- billing
- engineering
- security

Rules:
1. Only output ONE action.
2. Use EXACT strings from above.
3. Never output free text.
4. If unsure, choose best possible valid action.

Examples:

Ticket: "I was charged and want a refund"
Output:
{"action_type":"tag_issue","value":"billing_refund"}

Ticket: "Export reports not working"
Output:
{"action_type":"tag_issue","value":"product_bug"}

Ticket: "Unauthorized login detected"
Output:
{"action_type":"tag_issue","value":"security_compromise"}
"""


def build_prompt(obs: dict) -> str:
    step = obs["step_count"]

    if step == 0:
        guidance = "Start by identifying the issue using tag_issue."
    elif step == 1:
        guidance = "Set the correct priority."
    elif step == 2:
        guidance = "Assign the correct team."
    elif step == 3:
        guidance = "Ask for missing information if needed."
    elif step == 4:
        guidance = "Draft a response."
    else:
        guidance = "Resolve only if ready, escalate for security issues."

    return f"""
Task ID: {obs['task_id']}
Title: {obs['title']}
Difficulty: {obs['difficulty']}

Ticket:
{obs['ticket']}

Customer tier: {obs['customer_tier']}

Metadata:
{json.dumps(obs['metadata'], ensure_ascii=False)}

Visible policies:
{json.dumps(obs['visible_policy_snippets'], ensure_ascii=False)}

Current status: {obs['current_status']}

History:
{json.dumps(obs['history'], ensure_ascii=False)}

Step: {obs['step_count']} / {obs['max_steps']}

Guidance:
{guidance}

Return ONLY JSON with keys action_type and value.
If no value needed, use null.
"""


def call_model(client, obs: dict) -> dict:
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": build_prompt(obs)},
    ]

    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=messages,
            temperature=TEMPERATURE,
            max_tokens=120,
        )

        text = response.choices[0].message.content.strip()
        print("\nMODEL OUTPUT:", text)

        # extract JSON safely
        json_match = re.search(r"\{.*\}", text, re.DOTALL)
        if not json_match:
            raise ValueError("No JSON found")

        action = json.loads(json_match.group(0))

        # validate action
        allowed_actions = {
            "inspect_policy",
            "tag_issue",
            "set_priority",
            "assign_team",
            "ask_customer_question",
            "draft_reply",
            "escalate",
            "resolve_ticket",
        }

        if "action_type" not in action:
            raise ValueError("Missing action_type")

        if action["action_type"] not in allowed_actions:
            raise ValueError(f"Invalid action_type: {action['action_type']}")

        if "value" not in action:
            action["value"] = None

        print("ACTION SENT:", action)

        return action

    except Exception as e:
        print("ERROR:", e)
        return {"action_type": "inspect_policy", "value": None}


def run_task(client, task_id: str):
    print(f"\n===== RUNNING TASK: {task_id} =====")

    obs = requests.post(f"{ENV_BASE_URL}/reset", json={"task_id": task_id}).json()

    for step in range(MAX_STEPS):
        print(f"\n--- STEP {step} ---")

        action = call_model(client, obs)

        result = requests.post(f"{ENV_BASE_URL}/step", json=action).json()

        obs = result["observation"]

        print("REWARD:", result["reward"]["value"], "| DONE:", result["done"])

        if result["done"]:
            break

    grader = requests.get(f"{ENV_BASE_URL}/grader").json()

    return {
        "task_id": task_id,
        "score": grader["score"],
        "grader": grader,
    }


def main():
    client = OpenAI(base_url=API_BASE_URL, api_key=HF_TOKEN)

    results = [run_task(client, tid) for tid in TASK_IDS]

    avg = sum(r["score"] for r in results) / len(results)

    print("\nFINAL RESULT:")
    print(json.dumps({"results": results, "average_score": avg}, indent=2))


if __name__ == "__main__":
    main()