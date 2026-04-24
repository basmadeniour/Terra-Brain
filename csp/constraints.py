from models.city_graph import CityGraph

NON_PLANTABLE_LAND = ['building', 'road', 'water', 'industrial', 
                       'commercial', 'tundra', 'desert', 'barren']


def budget_constraint(decisions, max_trees):
    return sum(1 for v in decisions.values() if v == 1) <= max_trees


def land_constraint(location):
    return location.is_plantable()


def capacity_constraint(location):
    return location.can_plant_more()


def pollution_constraint(location, min_pollution=30):
    return location.pollution >= min_pollution


def distance_constraint(loc1, loc2, min_distance_meters=10):
    pos1 = loc1.get_location()
    pos2 = loc2.get_location()
    distance = CityGraph.calculate_distance(pos1, pos2)
    return distance >= min_distance_meters


def composite_constraint(state, decisions, max_trees=100, min_distance=10):
    if not budget_constraint(decisions, max_trees):
        return False
    
    plantable_locations = []
    for loc in state.locations:
        if decisions.get(loc.node_id, 0) == 1:
            if not land_constraint(loc):
                return False
            if not capacity_constraint(loc):
                return False
            plantable_locations.append(loc)
    
    for i in range(len(plantable_locations)):
        for j in range(i + 1, len(plantable_locations)):
            if not distance_constraint(plantable_locations[i], 
                                       plantable_locations[j], 
                                       min_distance):
                return False
    
    return True