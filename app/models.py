from typing import List, Dict, Optional, Literal, Any
from pydantic import BaseModel, Field

ActionType = Literal[
    "inspect_policy",
    "tag_issue",
    "set_priority",
    "assign_team",
    "ask_customer_question",
    "draft_reply",
    "escalate",
    "resolve_ticket",
]

class Action(BaseModel):
    action_type: ActionType
    value: Optional[str] = None

class Reward(BaseModel):
    value: float
    components: Dict[str, float] = Field(default_factory=dict)
    explanation: str = ""

class Observation(BaseModel):
    task_id: str
    title: str
    difficulty: str
    ticket: str
    customer_tier: str
    metadata: Dict[str, Any]
    visible_policy_snippets: List[str]
    current_status: str
    allowed_actions: List[str]
    step_count: int
    max_steps: int
    history: List[str] = Field(default_factory=list)

class EnvState(BaseModel):
    task_id: str
    step_count: int
    max_steps: int
    done: bool
    current_status: str
    tag: Optional[str] = None
    priority: Optional[str] = None
    assigned_team: Optional[str] = None
    escalated: bool = False
    resolved: bool = False
    questions_asked: List[str] = Field(default_factory=list)
    drafted_replies: List[str] = Field(default_factory=list)
    viewed_policies: int = 0
    action_history: List[Dict[str, Any]] = Field(default_factory=list)
    cumulative_reward: float = 0.0
    final_score: Optional[float] = None

class GraderResult(BaseModel):
    score: float
    breakdown: Dict[str, float]
    passed: bool