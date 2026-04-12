import os
import json
import re
from typing import List, Optional

import time
from openai import OpenAI
import requests
import subprocess


API_BASE_URL = os.getenv("API_BASE_URL", "https://router.huggingface.co/v1")
MODEL_NAME = os.getenv("MODEL_NAME", "Qwen/Qwen2.5-72B-Instruct")
HF_TOKEN = os.getenv("HF_TOKEN")
ENV_BASE_URL = os.getenv("ENV_BASE_URL", "http://127.0.0.1:7860")

MAX_STEPS = 8
TEMPERATURE = 0.0
TASK_IDS = ["easy_refund", "medium_bug", "hard_security"]
BENCHMARK = "support_ticket_triage"

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
""".strip()


def log_start(task: str, env: str, model: str) -> None:
    print(f"[START] task={task} env={env} model={model}", flush=True)


def log_step(step: int, action: str, reward: float, done: bool, error: Optional[str]) -> None:
    error_val = error if error else "null"
    done_val = str(done).lower()
    print(
        f"[STEP] step={step} action={action} reward={reward:.2f} done={done_val} error={error_val}",
        flush=True,
    )


def log_end(success: bool, steps: int, rewards: List[float]) -> None:
    rewards_str = ",".join(f"{r:.2f}" for r in rewards)
    print(f"[END] success={str(success).lower()} steps={steps} rewards={rewards_str}", flush=True)


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
If no value is needed, use null.
""".strip()


def call_model(client: OpenAI, obs: dict) -> dict:
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

        text = (response.choices[0].message.content or "").strip()

        json_match = re.search(r"\{.*\}", text, re.DOTALL)
        if not json_match:
            raise ValueError("No JSON found")

        action = json.loads(json_match.group(0))

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

        return action

    except Exception:
        return {"action_type": "inspect_policy", "value": None}


def action_to_str(action: dict) -> str:
    return json.dumps(action, ensure_ascii=False, separators=(",", ":"))


def start_server():
    return subprocess.Popen(
        ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "7860"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

def wait_for_server():
    for _ in range(15):
        try:
            r = requests.get(f"{ENV_BASE_URL}/health", timeout=2)
            if r.status_code == 200:
                return
        except:
            pass
        time.sleep(2)
    raise Exception("Server not reachable")

# ------------------ RUN TASK ------------------

def run_task(client: OpenAI, task_id: str) -> dict:
    rewards: List[float] = []
    steps_taken = 0
    success = False

    log_start(task=task_id, env=BENCHMARK, model=MODEL_NAME)

    try:
        # ✅ SAFE RESET
        try:
            response = requests.post(
                f"{ENV_BASE_URL}/reset",
                json={"task_id": task_id},
                timeout=5
            )
            response.raise_for_status()
            obs = response.json()
        except Exception as e:
            print("RESET ERROR:", str(e), flush=True)
            return {"task_id": task_id, "score": 0.01, "error": str(e)}

        for step in range(1, MAX_STEPS + 1):
            action = call_model(client, obs)
            action_str = action_to_str(action)

            # ✅ SAFE STEP
            try:
                response = requests.post(
                    f"{ENV_BASE_URL}/step",
                    json=action,
                    timeout=5
                )
                response.raise_for_status()
                result = response.json()
            except Exception as e:
                print("STEP ERROR:", str(e), flush=True)
                break

            obs = result.get("observation", {})
            reward = float(result.get("reward", {}).get("value", 0))
            done = bool(result.get("done", False))

            rewards.append(reward)
            steps_taken = step

            log_step(
                step=step,
                action=action_str,
                reward=reward,
                done=done,
                error=None,
            )

            if done:
                break

        # ✅ SAFE GRADER
        try:
            response = requests.get(f"{ENV_BASE_URL}/grader", timeout=5)
            response.raise_for_status()
            grader = response.json()
            score = float(grader.get("score", 0))
            # Clamp to strict (0, 1) open interval
            score = max(0.01, min(0.99, score))
            success = score >= 0.5
        except Exception as e:
            print("GRADER ERROR:", str(e), flush=True)
            score = 0.01

        return {
            "task_id": task_id,
            "score": score,
        }

    finally:
        log_end(success=success, steps=steps_taken, rewards=rewards)

# ------------------ MAIN ------------------

def main():
    if not HF_TOKEN:
        raise ValueError("HF_TOKEN environment variable is required")

    # ✅ START SERVER
    server_process = start_server()

    try:
        # ✅ WAIT FOR SERVER
        wait_for_server()

        client = OpenAI(base_url=API_BASE_URL, api_key=HF_TOKEN)

        for tid in TASK_IDS:
            run_task(client, tid)

    finally:
        # ✅ CLEANUP
        server_process.terminate()

# ------------------ ENTRY ------------------

if __name__ == "__main__":
    main()