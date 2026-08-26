import pytest
from app.evaluation.evaluator import SystemEvaluator
from app.evaluation.dataset import AGGREGATE_BENCHMARK_DATA, RouterTestCase, FactCheckTestCase
from app.agents.query_agent import QueryRoute
from app.agents.fact_checker import FactCheckResult

class MockQueryAgent:
    def route_query(self, query: str):
        if "percentage" in query or "How many" in query:
            return QueryRoute(query_type="aggregate")
        elif "Compare" in query:
            return QueryRoute(query_type="compare")
        elif "weather" in query:
            return QueryRoute(query_type="unsupported")
        return QueryRoute(query_type="retrieve")

class MockFactChecker:
    def verify(self, claim: str, evidence: list):
        if not evidence:
            return FactCheckResult(status="unverified", reasoning="No evidence")
        if "All analyzed" in claim:
            return FactCheckResult(status="unverified", reasoning="Evidence contradicts claim")
        return FactCheckResult(status="verified", reasoning="Supported by evidence")

def test_system_evaluator_deterministic_aggregate():
    evaluator = SystemEvaluator()
    res = evaluator.evaluate_aggregate_engine(AGGREGATE_BENCHMARK_DATA)
    assert res["accuracy_percentage"] == 100.0
    assert res["correct_predictions"] == len(AGGREGATE_BENCHMARK_DATA)

def test_system_evaluator_router_with_mock():
    evaluator = SystemEvaluator(query_agent=MockQueryAgent())
    res = evaluator.evaluate_router()
    assert res["accuracy_percentage"] == 100.0

def test_system_evaluator_fact_checker_with_mock():
    evaluator = SystemEvaluator(fact_checker=MockFactChecker())
    res = evaluator.evaluate_fact_checker()
    assert res["accuracy_percentage"] == 100.0
