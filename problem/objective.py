"""
Objective Function for Urban Green AI
Maximize environmental benefit from tree planting
"""

def objective_function(state, decisions):
    """
    Calculate the total environmental score based on decisions
    
    Args:
        state: State object containing locations
        decisions: dict {location_id: 0/1} where 1 means plant tree
    
    Returns:
        float: Total environmental score
    """
    total_score = 0.0
    
    # First, apply all tree effects (temporary)
    original_trees = {}
    for loc in state.locations:
        if decisions.get(loc.node_id, 0) == 1:
            original_trees[loc.node_id] = loc.planted_trees
            loc.plant_tree(effect=1.0)
    
    # Calculate score for all locations
    for loc in state.locations:
        total_score += loc.score
    
    # Revert tree effects
    for loc in state.locations:
        if decisions.get(loc.node_id, 0) == 1:
            loc.planted_trees = original_trees[loc.node_id]
            loc.update_score()
    
    return total_score


def calculate_benefit(state, decisions):
    """
    Calculate benefit with different weighting (for optimization)
    
    Args:
        state: State object
        decisions: dict of decisions
    
    Returns:
        float: Weighted benefit score
    """
    total_benefit = 0.0
    
    for loc in state.locations:
        if decisions.get(loc.node_id, 0) == 1:
            # Benefit from planting a tree
            pollution_reduction = min(50, loc.pollution * 0.3)
            temperature_reduction = min(10, loc.temperature * 0.2)
            benefit = pollution_reduction * 0.6 + temperature_reduction * 0.4
            total_benefit += benefit
    
    return total_benefit