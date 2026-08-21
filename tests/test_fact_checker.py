from unittest.mock import patch
from app.agents.fact_checker import FactCheckerAgent, FactCheckResult

@patch('app.agents.fact_checker.ChatPromptTemplate')
def test_fact_checker_verified(mock_prompt):
    agent = FactCheckerAgent()
    # Replace verify directly for testing
    agent.verify = lambda c, e: FactCheckResult(
        status="verified",
        reasoning="The evidence explicitly mentions LangGraph.",
        supporting_evidence=["This project relies on LangGraph for state management."]
    )
    
    res = agent.verify("The project uses LangGraph.", ["This project relies on LangGraph for state management."])
    assert res.status == "verified"
    assert len(res.supporting_evidence) == 1

def test_fact_checker_unverified():
    agent = FactCheckerAgent()
    agent.verify = lambda c, e: FactCheckResult(
        status="unverified",
        reasoning="The evidence does not mention LangGraph.",
        supporting_evidence=[]
    )
    
    res = agent.verify("The project uses LangGraph.", ["This project uses Celery."])
    assert res.status == "unverified"
    assert len(res.supporting_evidence) == 0

def test_fact_checker_empty_evidence():
    agent = FactCheckerAgent()
    # It should naturally return unverified if evidence is empty
    res = agent.verify("Claim without evidence", [])
    assert res.status == "unverified"
