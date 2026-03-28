from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional

from app.env import SupportTicketTriageEnv
from app.models import Action
from app.tasks import TASKS
from app.graders import grade_task

app = FastAPI(title="Support Ticket Triage OpenEnv")

ENV = SupportTicketTriageEnv(max_steps=8)

class ResetRequest(BaseModel):
    task_id: Optional[str] = "easy_refund"

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/tasks")
def tasks():
    return {
        "tasks": [
            {
                "task_id": t["task_id"],
                "title": t["title"],
                "difficulty": t["difficulty"]
            }
            for t in TASKS.values()
        ],
        "action_schema": {
            "action_type": [
                "inspect_policy",
                "tag_issue",
                "set_priority",
                "assign_team",
                "ask_customer_question",
                "draft_reply",
                "escalate",
                "resolve_ticket",
            ],
            "value": "optional string"
        }
    }

@app.post("/reset")
def reset(req: ResetRequest):
    obs = ENV.reset(task_id=req.task_id)
    return obs.model_dump()

@app.post("/step")
def step(action: Action):
    obs, reward, done, info = ENV.step(action)
    return {
        "observation": obs.model_dump(),
        "reward": reward.model_dump(),
        "done": done,
        "info": info
    }

@app.get("/state")
def state():
    return ENV.state().model_dump()

@app.get("/grader")
def grader():
    state_obj = ENV.state()
    task = TASKS[state_obj.task_id]
    return grade_task(task, state_obj)