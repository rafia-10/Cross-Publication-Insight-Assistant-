from typing import List, Dict, Any

def calculate_percentage(matches: int, total: int) -> Dict[str, Any]:
    """
    Deterministically calculates the percentage of matches out of a total.
    """
    if total == 0:
        return {"matching": matches, "total": total, "percentage": 0.0}
    
    percentage = (matches / total) * 100.0
    return {
        "matching": matches,
        "total": total,
        "percentage": round(percentage, 2)
    }

def aggregate_technologies(projects_analysis: List[Dict[str, Any]], target_attribute: str, target_value: str) -> Dict[str, Any]:
    """
    Counts how many projects in the given list use a specific technology (target_value)
    within a given attribute category (target_attribute).
    
    Example: target_attribute="frameworks", target_value="LangGraph"
    """
    matching_projects = []
    
    for project in projects_analysis:
        # Expected structure: project is a dict representation of ProjectAnalysis
        attributes = project.get(target_attribute, [])
        
        has_match = False
        for tech in attributes:
            # tech is a dict of TechnologyEvidence
            if tech.get("technology", "").lower() == target_value.lower():
                has_match = True
                break
                
        if has_match:
            matching_projects.append({
                "project_name": project.get("project_name"),
                "source_url": project.get("source_url")
            })
            
    result = calculate_percentage(len(matching_projects), len(projects_analysis))
    result["matching_projects"] = matching_projects
    result["target_attribute"] = target_attribute
    result["target_value"] = target_value
    
    return result

def get_most_common_technologies(projects_analysis: List[Dict[str, Any]], target_attribute: str, top_n: int = 5) -> List[Dict[str, Any]]:
    """
    Finds the most frequently used technologies in a given attribute category.
    """
    counts = {}
    
    for project in projects_analysis:
        attributes = project.get(target_attribute, [])
        for tech in attributes:
            name = tech.get("technology")
            if not name:
                continue
            name_lower = name.lower()
            if name_lower not in counts:
                counts[name_lower] = {"name": name, "count": 0, "projects": []}
            
            counts[name_lower]["count"] += 1
            counts[name_lower]["projects"].append(project.get("project_name"))
            
    # Sort descending by count
    sorted_techs = sorted(counts.values(), key=lambda x: x["count"], reverse=True)
    return sorted_techs[:top_n]
