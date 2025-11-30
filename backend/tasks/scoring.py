from datetime import date
from dateutil.relativedelta import relativedelta

DEFAULT_WEIGHTS = {
    "urgency": 0.45,
    "importance": 0.35,
    "effort": 0.10,
    "dependency": 0.10,
}

STRATEGY_PRESETS = {
    "smart_balance": DEFAULT_WEIGHTS,
    "fastest_wins": {"urgency": 0.20, "importance": 0.20, "effort": 0.50, "dependency": 0.10},
    "high_impact": {"urgency": 0.20, "importance": 0.60, "effort": 0.10, "dependency": 0.10},
    "deadline_driven": {"urgency": 0.60, "importance": 0.20, "effort": 0.10, "dependency": 0.10},
}

def normalize(value, min_val, max_val, default=0.0):
    try:
        if value is None:
            return default
        if max_val == min_val:
            return default
        clamped = max(min(value, max_val), min_val)
        return (clamped - min_val) / (max_val - min_val)
    except Exception:
        return default

def compute_urgency(due_date):
    """Higher when due soon or past due. Handles None."""
    if due_date is None:
        return 0.2  # slight urgency for unknown deadlines
    today = date.today()
    delta_days = (due_date - today).days
    if delta_days < 0:
        # Past due: scale >1 then cap with normalization later
        # map: -30 days -> 1.0, -1 -> 0.6
        past_severity = min(30, abs(delta_days))
        return 0.6 + (past_severity / 30) * 0.4  # 0.6 to 1.0
    else:
        # Due in future: 0 to 0.8 (closer is higher)
        # 0 days -> 0.8, 30+ -> ~0.1
        future_window = min(delta_days, 60)
        return max(0.1, 0.8 - (future_window / 60) * 0.7)

def compute_importance(importance):
    """Importance 1-10 normalized to 0-1 with gentle boost for 8+."""
    if importance is None:
        return 0.3
    base = normalize(importance, 1, 10, default=0.3)
    if importance >= 8:
        base = min(1.0, base + 0.1)
    return base

def compute_effort_inverse(estimated_hours):
    """Lower effort => higher score. Handle None."""
    if estimated_hours is None:
        return 0.4
    # Map hours: 0-2 -> near 1.0, 8 -> ~0.4, 16+ -> ~0.1
    if estimated_hours <= 0:
        return 0.9
    capped = min(estimated_hours, 24)
    return max(0.1, 1.0 - (capped / 24) * 0.9)

def compute_dependency_boost(task_id, graph, indegree_map):
    """Tasks that unblock others rank higher. Use out-degree (how many depend on it)."""
    # Build reverse edges: dependents per node
    dependents_count = 0
    for other_id, deps in graph.items():
        if task_id in deps:
            dependents_count += 1
    # Normalize by size
    size = max(1, len(graph) - 1)
    ratio = dependents_count / size
    # Also slightly boost if this task has zero incoming deps (can start now)
    ready_boost = 0.1 if indegree_map.get(task_id, 0) == 0 else 0.0
    return min(1.0, ratio + ready_boost)

def detect_circular_dependencies(graph):
    """Return set of nodes involved in cycles using DFS."""
    visited = set()
    stack = set()
    in_cycle = set()

    def dfs(node):
        if node in stack:
            in_cycle.add(node)
            return
        if node in visited:
            return
        visited.add(node)
        stack.add(node)
        for nbr in graph.get(node, []):
            dfs(nbr)
        stack.remove(node)

    for node in graph.keys():
        dfs(node)

    # Expand: any node that reaches a cycle node is also suspect; for simplicity,
    # mark nodes that were in stack hits. Conservative detection.
    return in_cycle

def indegree(graph):
    counts = {k: 0 for k in graph.keys()}
    for k, deps in graph.items():
        for d in deps:
            if d in counts:
                counts[d] += 1
    return counts

def score_tasks(tasks, strategy="smart_balance", user_weights=None):
    """Main scoring function. Returns list enriched with score and explanation."""
    weights = STRATEGY_PRESETS.get(strategy, DEFAULT_WEIGHTS)
    if user_weights:
        # Merge user weights, then renormalize to sum to 1
        merged = {**weights, **user_weights}
        total = sum(merged.values()) or 1.0
        weights = {k: v / total for k, v in merged.items()}

    # Build dependency graph by provided IDs (string IDs optional)
    graph = {}
    ids = []
    for t in tasks:
        tid = t.get("id") or t.get("title")  # fallback to title as pseudo-id
        ids.append(tid)
        deps = t.get("dependencies") or []
        # Only keep deps that reference existing tasks
        graph[tid] = [d for d in deps if d is not None]

    cycle_nodes = detect_circular_dependencies(graph)
    indeg = indegree(graph)

    results = []
    for t in tasks:
        tid = t.get("id") or t.get("title")
        u = compute_urgency(t.get("due_date"))
        imp = compute_importance(t.get("importance"))
        eff_inv = compute_effort_inverse(t.get("estimated_hours"))
        dep = compute_dependency_boost(tid, graph, indeg)

        # Penalize cycle-involved tasks to avoid deadlocks unless urgent
        cycle_penalty = 0.15 if tid in cycle_nodes else 0.0
        raw = (
            weights["urgency"] * u
            + weights["importance"] * imp
            + weights["effort"] * eff_inv
            + weights["dependency"] * dep
        )
        score = max(0.0, raw - cycle_penalty)

        # Priority bands
        if score >= 0.75:
            band = "High"
        elif score >= 0.45:
            band = "Medium"
        else:
            band = "Low"

        # Explanation
        reasons = []
        if t.get("due_date") is None:
            reasons.append("Unknown due date reduced urgency confidence.")
        elif u >= 0.8:
            reasons.append("Due soon or past due increases urgency.")
        if t.get("importance") is None:
            reasons.append("Missing importance defaults to moderate impact.")
        elif t["importance"] >= 8:
            reasons.append("High importance boosts priority.")
        if t.get("estimated_hours") is None:
            reasons.append("Unknown effort assumes moderate time.")
        elif eff_inv >= 0.8:
            reasons.append("Low effort makes this a quick win.")
        if dep >= 0.6:
            reasons.append("Unblocks multiple tasks, increasing impact.")
        if tid in cycle_nodes:
            reasons.append("Detected circular dependency, applying safety penalty.")

        explanation = " ".join(reasons) if reasons else "Balanced by urgency, importance, effort, and dependencies."
        enriched = {
            **t,
            "id": tid,
            "score": round(score, 4),
            "priority_band": band,
            "explanation": explanation,
        }
        results.append(enriched)

    # Sort descending by score, tiebreakers: earlier due_date, higher importance, lower effort
    def sort_key(x):
        dd = x.get("due_date")
        dd_tuple = (0, date.max) if dd is None else (1, dd)
        imp = x.get("importance") or 0
        eff = x.get("estimated_hours") or 999
        return (-x["score"], dd_tuple, -imp, eff)

    results.sort(key=sort_key)
    return results

def top_suggestions(tasks, strategy="smart_balance", user_weights=None, k=3):
    all_scored = score_tasks(tasks, strategy=strategy, user_weights=user_weights)
    return all_scored[:k]