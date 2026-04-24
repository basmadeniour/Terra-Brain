"""
Decision Variables Definition
"""

def initialize_decisions(state, default_value=0):
    """
    Initialize decision variables for all locations
    
    Args:
        state: State object
        default_value: Default value (0 or 1)
    
    Returns:
        dict: {location_id: value}
    """
    return {loc.node_id: default_value for loc in state.locations}


def get_decision_domain(location):
    """
    Get allowed values for a location's decision variable
    
    Args:
        location: Location object
    
    Returns:
        list: [0, 1] if plantable, [0] otherwise
    """
    if location.is_plantable() and location.can_plant_more():
        return [0, 1]
    return [0]


def count_planted_trees(decisions):
    """Count how many trees are planted in the decision set"""
    return sum(1 for v in decisions.values() if v == 1)