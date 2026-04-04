import os
import json
from openai import OpenAI
import requests

API_BASE_URL = os.getenv("API_BASE_URL", "https://router.huggingface.co/v1")
HF_TOKEN = os.getenv("HF_TOKEN") or os.getenv("API_KEY")
MODEL_NAME = os.getenv("MODEL_NAME")
ENV_BASE_URL = os.getenv("ENV_BASE_URL", "http://127.0.0.1:8000")

MAX_STEPS = 8
TEMPERATURE = 0.2
TASK_IDS = ["easy_refund", "medium_bug", "hard_security"]

SYSTEM_PROMPT = """
You are an AI agent operating a customer support ticket triage environment.
You must reply with exactly one JSON object and nothing else.

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

Choose only one action at a time.
"""

def build_prompt(obs: dict) -> str:
    return f"""
Task ID: {obs['task_id']}
Title: {obs['title']}
Difficulty: {obs['difficulty']}
Ticket: {obs['ticket']}
Customer tier: {obs['customer_tier']}
Metadata: {json.dumps(obs['metadata'])}
Visible policies: {json.dumps(obs['visible_policy_snippets'])}
Current status: {obs['current_status']}
Allowed actions: {json.dumps(obs['allowed_actions'])}
History: {json.dumps(obs['history'])}
Step: {obs['step_count']} / {obs['max_steps']}
"""

def call_model(client, obs: dict) -> dict:
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": build_prompt(obs)}
    ]

    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=messages,
            temperature=TEMPERATURE,
            max_tokens=150,
        )
        text = response.choices[0].message.content.strip()
        action = json.loads(text)
        return action
    except Exception:
        return {"action_type": "inspect_policy", "value": None}

def run_task(client, task_id: str):
    obs = requests.post(f"{ENV_BASE_URL}/reset", json={"task_id": task_id}).json()

    for _ in range(MAX_STEPS):
        action = call_model(client, obs)
        result = requests.post(f"{ENV_BASE_URL}/step", json=action).json()
        obs = result["observation"]
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
    print(json.dumps({"results": results, "average_score": avg}, indent=2))

if __name__ == "__main__":
    main()