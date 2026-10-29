def battery_state(percentage: float) -> dict[str, str | float]:
    if percentage <= 15:
        return {
            "level": "CRITICAL",
            "label": "Charge now",
            "message": "Battery is critically low; stop and recharge before another leg.",
            "percentage": round(percentage, 2),
        }
    if percentage <= 30:
        return {
            "level": "LOW",
            "label": "Charge soon",
            "message": "Battery is low; finish only a short safe leg, then recharge.",
            "percentage": round(percentage, 2),
        }
    return {
        "level": "HEALTHY",
        "label": "Sufficient",
        "message": "Battery reserve is sufficient for the current plan.",
        "percentage": round(percentage, 2),
    }


def enrich_route_result(result: dict) -> dict:
    if result.get("success"):
        result["battery_state"] = battery_state(result["remaining_battery"])
    return result
