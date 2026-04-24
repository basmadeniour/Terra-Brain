"""
Problem State Definition for Urban Green AI
"""

class State:
    """Represents the complete state of the urban environment"""
    
    def __init__(self, city_graph):
        """
        Args:
            city_graph: CityGraph object containing all locations
        """
        self.city_graph = city_graph
        self.locations = list(city_graph.nodes.values()) if city_graph else []
    
    def get_location_by_id(self, location_id):
        """Get location by its node ID"""
        return self.city_graph.nodes.get(location_id)
    
    def get_plantable_locations(self):
        """Get only locations that can potentially have trees"""
        return [loc for loc in self.locations if loc.is_plantable()]
    
    def get_decision_variables(self):
        """Return list of all location IDs (decision variables)"""
        return [loc.node_id for loc in self.locations]
    
    def get_initial_decisions(self):
        """Initialize all decisions to 0 (no trees)"""
        return {loc.node_id: 0 for loc in self.locations}
    
    def copy(self):
        """Create a deep copy of the state"""
        import copy
        return copy.deepcopy(self)
    
    def __len__(self):
        return len(self.locations)
    
    def __iter__(self):
        return iter(self.locations)