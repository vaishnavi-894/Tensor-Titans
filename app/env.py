from typing import Optional, Dict, Any
from copy import deepcopy

from app.tasks import TASKS
from app.models import Observation, Action, Reward, EnvState
from app.rewards import compute_reward
from app.graders import grade_task

class SupportTicketTriageEnv:
    def __init__(self, max_steps: int = 8):
        self.max_steps = max_steps
        self.current_task: Optional[Dict[str, Any]] = None
        self.state_obj: Optional[EnvState] = None

    def _build_observation(self) -> Observation:
        task = self.current_task
        return Observation(
            task_id=task["task_id"],
            title=task["title"],
            difficulty=task["difficulty"],
            ticket=task["ticket"],
            customer_tier=task["customer_tier"],
            metadata=task["metadata"],
            visible_policy_snippets=task["policy_snippets"],
            current_status=self.state_obj.current_status,
            allowed_actions=[
                "inspect_policy",
                "tag_issue",
                "set_priority",
                "assign_team",
                "ask_customer_question",
                "draft_reply",
                "escalate",
                "resolve_ticket",
            ],
            step_count=self.state_obj.step_count,
            max_steps=self.state_obj.max_steps,
            history=[
                f"{x['action_type']}::{x.get('value', '')}"
                for x in self.state_obj.action_history
            ],
        )

    def reset(self, task_id: str = "easy_refund") -> Observation:
        if task_id not in TASKS:
            raise ValueError(f"Unknown task_id: {task_id}")

        self.current_task = deepcopy(TASKS[task_id])
        self.state_obj = EnvState(
            task_id=task_id,
            step_count=0,
            max_steps=self.max_steps,
            done=False,
            current_status="open"
        )
        return self._build_observation()

    def step(self, action: Action):
        if self.state_obj is None or self.current_task is None:
            raise RuntimeError("Call reset() before step().")

        if self.state_obj.done:
            return self._build_observation(), Reward(value=0.0, explanation="Episode already done."), True, {
                "warning": "Episode already completed."
            }

        self.state_obj.step_count += 1
        self.state_obj.action_history.append(action.model_dump())

        if action.action_type == "inspect_policy":
            self.state_obj.viewed_policies += 1

        elif action.action_type == "tag_issue":
            self.state_obj.tag = action.value

        elif action.action_type == "set_priority":
            self.state_obj.priority = action.value

        elif action.action_type == "assign_team":
            self.state_obj.assigned_team = action.value

        elif action.action_type == "ask_customer_question":
            if action.value:
                self.state_obj.questions_asked.append(action.value)

        elif action.action_type == "draft_reply":
            if action.value:
                self.state_obj.drafted_replies.append(action.value)

        elif action.action_type == "escalate":
            self.state_obj.escalated = True
            self.state_obj.current_status = "escalated"

        elif action.action_type == "resolve_ticket":
            self.state_obj.resolved = True
            self.state_obj.current_status = "resolved"

        reward_data = compute_reward(self.current_task, self.state_obj, action)
        reward = Reward(**reward_data)
        self.state_obj.cumulative_reward += reward.value

        done = False
        info = {}

        if action.action_type in ["resolve_ticket", "escalate"]:
            done = True

        if self.state_obj.step_count >= self.state_obj.max_steps:
            done = True

        if done:
            self.state_obj.done = True
            grade = grade_task(self.current_task, self.state_obj)
            self.state_obj.final_score = grade["score"]
            info["grader"] = grade

        return self._build_observation(), reward, done, info

    def state(self) -> EnvState:
        if self.state_obj is None:
            raise RuntimeError("Call reset() before state().")
        return self.state_obj