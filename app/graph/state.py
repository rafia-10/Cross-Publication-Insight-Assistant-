from typing import TypedDict, List, Dict, Any, Optional

class GraphState(TypedDict):
    # Input
    user_query: str
    project_ids: Optional[List[int]]
    
    # Routing
    query_type: Optional[str]          # aggregate | retrieve | compare | unsupported
    target_attribute: Optional[str]
    target_value: Optional[str]
    search_terms: Optional[List[str]]
    
    # Retrieved data
    projects_analysis: Optional[List[Dict[str, Any]]]
    retrieved_chunks: Optional[List[Dict[str, Any]]]
    
    # Results from each path
    aggregate_result: Optional[Dict[str, Any]]
    rag_result: Optional[List[Dict[str, Any]]]
    compare_result: Optional[Dict[str, Any]]
    
    # Verification
    fact_check_result: Optional[Dict[str, Any]]
    
    # Final output
    final_answer: Optional[str]
    error: Optional[str]
