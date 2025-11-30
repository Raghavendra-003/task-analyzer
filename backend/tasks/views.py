from rest_framework.decorators import api_view
from rest_framework.response import Response
from datetime import datetime

@api_view(["POST"])
def analyze_tasks(request):
    tasks = request.data.get("tasks", [])
    strategy = request.data.get("strategy", "smart_balance")

    results = []
    for t in tasks:
        score = 0.0
        explanation = []

        # Parse due date safely
        due_date = t.get("due_date")
        days_left = None
        if due_date:
            try:
                days_left = (datetime.strptime(due_date, "%Y-%m-%d") - datetime.today()).days
            except Exception:
                days_left = None

        hours = t.get("estimated_hours", 0)
        importance = t.get("importance", 5)

        # Strategy-specific scoring
        if strategy == "fastest_wins":
            score = max(0, 1 - (hours / 10))
            explanation.append("Fastest Wins: lower effort tasks score higher.")
        elif strategy == "high_impact":
            score = importance / 10
            explanation.append("High Impact: importance drives priority.")
        elif strategy == "deadline_driven":
            if days_left is not None:
                score = max(0, 1 - (days_left / 30))
                explanation.append("Deadline Driven: tasks due sooner score higher.")
            else:
                score = 0.5
                explanation.append("Deadline Driven: no due date, neutral score.")
        else:  # smart_balance
            score = 0.3
            if days_left is not None and days_left <= 7:
                score += 0.3
                explanation.append("Due soon increases urgency.")
            if hours and hours <= 3:
                score += 0.2
                explanation.append("Low effort makes this a quick win.")
            if importance and importance >= 8:
                score += 0.2
                explanation.append("High importance boosts priority.")

        # Assign priority band
        if score >= 0.8:
            band = "High"
        elif score >= 0.6:
            band = "Medium"
        else:
            band = "Low"

        results.append({
            "title": t.get("title"),
            "priority_band": band,
            "score": round(score, 2),
            "due_date": due_date,
            "estimated_hours": hours,
            "importance": importance,
            "dependencies": t.get("dependencies", []),
            "explanation": " ".join(explanation) or "No special factors detected."
        })

    return Response({"results": results})