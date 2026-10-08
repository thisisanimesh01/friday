def require_confirmation(action: str, action_type: str = None, target: str = None) -> dict:
    data = {
        "status": "confirmation_required",
        "message": f"Are you sure you want to {action}? (yes/no)"
    }
    if action_type:
        data["action_type"] = action_type
    if target:
        data["target"] = target
    return data

def confirm_action(user_input: str) -> bool:
    return user_input.strip().lower() in ["yes", "y"]