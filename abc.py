from app.env import SupportTicketTriageEnv
from app.models import Action

env = SupportTicketTriageEnv(max_steps=8)

obs = env.reset("easy_refund")
print(obs)

obs, reward, done, info = env.step(Action(action_type="tag_issue", value="billing_refund"))
print(reward, done)

obs, reward, done, info = env.step(Action(action_type="set_priority", value="medium"))
print(reward, done)

obs, reward, done, info = env.step(Action(action_type="assign_team", value="billing"))
print(reward, done)

obs, reward, done, info = env.step(Action(action_type="ask_customer_question", value="Please share your order ID or invoice receipt."))
print(reward, done)

obs, reward, done, info = env.step(Action(action_type="draft_reply", value="We can help with your refund. Please share your order or invoice for verification."))
print(reward, done)

obs, reward, done, info = env.step(Action(action_type="resolve_ticket"))
print(reward, done, info)