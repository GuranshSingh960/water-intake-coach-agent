from memory import memory


def log_water(ml):
    memory["water_consumed"] += ml

    return {
        "consumed": memory["water_consumed"],
        "goal": memory["daily_goal"]
    }


def get_progress():
    consumed = memory["water_consumed"]
    goal = memory["daily_goal"]

    return {
        "consumed": consumed,
        "goal": goal,
        "remaining": max(goal - consumed, 0)
    }