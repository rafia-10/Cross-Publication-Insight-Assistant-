import time
from typing import Dict, Any, List
from app.evaluation.dataset import (
    ROUTER_BENCHMARK_DATA,
    FACT_CHECK_BENCHMARK_DATA,
    AGGREGATE_BENCHMARK_DATA,
)
from app.agents.query_agent import QueryAgent
from app.agents.fact_checker import FactCheckerAgent
from app.tools.aggregate_calculations import aggregate_technologies

class SystemEvaluator:
    def __init__(self, query_agent: QueryAgent = None, fact_checker: FactCheckerAgent = None):
        self.query_agent = query_agent or QueryAgent()
        self.fact_checker = fact_checker or FactCheckerAgent()

    def evaluate_router(self, test_cases: List[Any] = None) -> Dict[str, Any]:
        """Evaluates query classification precision and accuracy."""
        cases = test_cases or ROUTER_BENCHMARK_DATA
        total = len(cases)
        correct = 0
        details = []

        start_time = time.time()
        for case in cases:
            route = self.query_agent.route_query(case.query)
            is_match = route.query_type == case.expected_type
            if is_match:
                correct += 1
            details.append({
                "query": case.query,
                "expected": case.expected_type,
                "predicted": route.query_type,
                "passed": is_match,
            })
        duration = time.time() - start_time

        accuracy = (correct / total) * 100 if total > 0 else 0.0
        return {
            "metric": "Query Routing Accuracy",
            "total_samples": total,
            "correct_predictions": correct,
            "accuracy_percentage": round(accuracy, 2),
            "execution_time_seconds": round(duration, 3),
            "details": details,
        }

    def evaluate_fact_checker(self, test_cases: List[Any] = None) -> Dict[str, Any]:
        """Evaluates Fact-Checker verification correctness against ground-truth claims."""
        cases = test_cases or FACT_CHECK_BENCHMARK_DATA
        total = len(cases)
        correct = 0
        details = []

        start_time = time.time()
        for case in cases:
            res = self.fact_checker.verify(case.claim, case.evidence)
            # Accept if exact match or correctly flagged unverified/partial
            is_match = (res.status == case.expected_status)
            if is_match:
                correct += 1
            details.append({
                "claim": case.claim,
                "expected_status": case.expected_status,
                "predicted_status": res.status,
                "reasoning": res.reasoning,
                "passed": is_match,
            })
        duration = time.time() - start_time

        accuracy = (correct / total) * 100 if total > 0 else 0.0
        return {
            "metric": "Fact-Checker Verification Accuracy",
            "total_samples": total,
            "correct_predictions": correct,
            "accuracy_percentage": round(accuracy, 2),
            "execution_time_seconds": round(duration, 3),
            "details": details,
        }

    def evaluate_aggregate_engine(self, test_cases: List[Any] = None) -> Dict[str, Any]:
        """Evaluates mathematical determinism and calculation precision of aggregation."""
        cases = test_cases or AGGREGATE_BENCHMARK_DATA
        total = len(cases)
        correct = 0
        details = []

        start_time = time.time()
        for case in cases:
            res = aggregate_technologies(case.projects, case.attribute, case.target_value)
            count_match = res["matching"] == case.expected_count
            pct_match = abs(res["percentage"] - case.expected_percentage) < 0.01
            is_match = count_match and pct_match
            if is_match:
                correct += 1
            details.append({
                "target_value": case.target_value,
                "expected_count": case.expected_count,
                "predicted_count": res["matching"],
                "expected_percentage": case.expected_percentage,
                "predicted_percentage": res["percentage"],
                "passed": is_match,
            })
        duration = time.time() - start_time

        accuracy = (correct / total) * 100 if total > 0 else 0.0
        return {
            "metric": "Deterministic Aggregation Precision",
            "total_samples": total,
            "correct_predictions": correct,
            "accuracy_percentage": round(accuracy, 2),
            "execution_time_seconds": round(duration, 4),
            "details": details,
        }

    def run_all(self) -> Dict[str, Any]:
        """Runs the entire evaluation suite and returns composite benchmark results."""
        return {
            "router_evaluation": self.evaluate_router(),
            "fact_checker_evaluation": self.evaluate_fact_checker(),
            "aggregate_evaluation": self.evaluate_aggregate_engine(),
        }
