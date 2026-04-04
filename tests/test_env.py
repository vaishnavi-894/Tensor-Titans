from app.env import SupportTicketTriageEnv
from app.models import Action

def test_reset_and_step():
    env = SupportTicketTriageEnv(max_steps=8)
    obs = env.reset("easy_refund")
    assert obs.task_id == "easy_refund"

    obs, reward, done, info = env.step(Action(action_type="inspect_policy"))
    assert isinstance(reward.value, float)
    assert done in [True, False]