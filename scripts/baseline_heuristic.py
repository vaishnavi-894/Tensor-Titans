from app.env import SupportTicketTriageEnv
from app.models import Action

def run_task(task_id):
    env = SupportTicketTriageEnv(max_steps=8)
    obs = env.reset(task_id)

    ticket = obs.ticket.lower()

    if "refund" in ticket or "charged" in ticket:
        actions = [
            Action(action_type="inspect_policy"),
            Action(action_type="tag_issue", value="billing_refund"),
            Action(action_type="set_priority", value="medium"),
            Action(action_type="assign_team", value="billing"),
            Action(action_type="ask_customer_question", value="Please share your order ID or invoice receipt."),
            Action(action_type="draft_reply", value="We can help with your refund. Please share the invoice or order details for verification."),
            Action(action_type="resolve_ticket"),
        ]

    elif "export reports" in ticket or "affecting" in ticket:
        actions = [
            Action(action_type="inspect_policy"),
            Action(action_type="tag_issue", value="product_bug"),
            Action(action_type="set_priority", value="high"),
            Action(action_type="assign_team", value="engineering"),
            Action(action_type="ask_customer_question", value="Please share reproduction steps, error details, and time of occurrence."),
            Action(action_type="draft_reply", value="Sorry for the impact. We are investigating and need steps, timestamps, and the exact error."),
            Action(action_type="resolve_ticket"),
        ]

    else:
        actions = [
            Action(action_type="inspect_policy"),
            Action(action_type="tag_issue", value="security_compromise"),
            Action(action_type="set_priority", value="urgent"),
            Action(action_type="assign_team", value="security"),
            Action(action_type="ask_customer_question", value="Please verify whether these were unauthorized logins and confirm recent account activity."),
            Action(action_type="draft_reply", value="This appears security-related. We are investigating and will help secure and verify your account."),
            Action(action_type="escalate"),
        ]

    final_info = {}
    for action in actions:
        obs, reward, done, info = env.step(action)
        final_info = info
        if done:
            break

    return {
        "task_id": task_id,
        "final_score": final_info.get("grader", {}).get("score", 0.01),
        "grader": final_info.get("grader", {})
    }

if __name__ == "__main__":
    results = [run_task(tid) for tid in ["easy_refund", "medium_bug", "hard_security"]]
    avg = sum(r["final_score"] for r in results) / len(results)
    print({"results": results, "average_score": avg})