def require_confirmation(action: str) -> dict:
    return {
        "status": "confirmation_required",
        "message": f"Are you sure you want to {action}? (yes/no)"
    }

def confirm_action(user_input: str) -> bool:
    return user_input.strip().lower() in ["yes", "y"]