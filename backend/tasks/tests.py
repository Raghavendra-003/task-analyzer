from django.test import TestCase
from datetime import date, timedelta
from .scoring import score_tasks, detect_circular_dependencies

class ScoringAlgorithmTests(TestCase):
    def test_past_due_tasks_get_higher_urgency(self):
        tasks = [
            {"id": "A", "title": "Past", "due_date": date.today() - timedelta(days=3), "estimated_hours": 4, "importance": 5, "dependencies": []},
            {"id": "B", "title": "Future", "due_date": date.today() + timedelta(days=7), "estimated_hours": 4, "importance": 5, "dependencies": []},
        ]
        scored = score_tasks(tasks)
        self.assertGreater(scored[0]["score"], scored[1]["score"])
        self.assertEqual(scored[0]["title"], "Past")

    def test_low_effort_quick_wins(self):
        tasks = [
            {"id": "A", "title": "Big task", "due_date": None, "estimated_hours": 16, "importance": 5, "dependencies": []},
            {"id": "B", "title": "Small task", "due_date": None, "estimated_hours": 1, "importance": 5, "dependencies": []},
        ]
        scored = score_tasks(tasks, strategy="fastest_wins")
        self.assertEqual(scored[0]["title"], "Small task")

    def test_circular_dependency_penalty(self):
        tasks = [
            {"id": "A", "title": "A", "due_date": None, "estimated_hours": 2, "importance": 7, "dependencies": ["B"]},
            {"id": "B", "title": "B", "due_date": None, "estimated_hours": 2, "importance": 7, "dependencies": ["A"]},
            {"id": "C", "title": "C", "due_date": None, "estimated_hours": 2, "importance": 7, "dependencies": []},
        ]
        scored = score_tasks(tasks)
        # C should outrank cycle A/B thanks to penalty
        top_titles = [t["title"] for t in scored[:2]]
        self.assertIn("C", top_titles)

class CycleDetectionTests(TestCase):
    def test_detects_cycle(self):
        graph = {"A": ["B"], "B": ["C"], "C": ["A"], "D": []}
        cycles = detect_circular_dependencies(graph)
        self.assertTrue("A" in cycles or "B" in cycles or "C" in cycles)
        self.assertFalse("D" in cycles)