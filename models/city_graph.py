import math
from typing import List, Tuple, Dict, Any, Optional
from models.location import Location


class CityGraph:
    
    DEFAULT_TREE_EFFECT_DISTANCE = 50
    DEFAULT_FACTORY_EFFECT_DISTANCE = 100
    DEFAULT_EDGE_MAX_DISTANCE = 2000
    
    def __init__(self, name: str = "Unknown City"):
        self.name = name
        self.nodes: Dict[str, Location] = {}
        self.edges: Dict[str, List[str]] = {}
        self.center_lat: float = 24.7136
        self.center_lon: float = 46.6753
    
    def _is_valid_planting_location(self, location: Location) -> bool:
        return location.is_plantable() and not location.is_factory and location.score > 10
    
    def get_best_locations(self, top_n: int = 10, use_computed_benefit: bool = True) -> List[Location]:
        nodes_list = list(self.nodes.values())
        key_func = lambda x: getattr(x, 'computed_benefit', x.score) if use_computed_benefit else lambda x: x.score
        sorted_nodes = sorted(nodes_list, key=key_func, reverse=True) if use_computed_benefit else sorted(nodes_list, key=lambda x: x.score, reverse=True)
        valid_nodes = [loc for loc in sorted_nodes if self._is_valid_planting_location(loc)]
        return valid_nodes[:top_n]
    
    def get_top_planting_candidates(self, n: int = 10) -> List[Dict[str, Any]]:
        candidates = []
        for loc in self.get_plantable_locations_with_scores():
            if loc['tree_capacity'] > 0:
                candidates.append(loc)
        return candidates[:n]
    
    def get_locations_by_score_range(self, min_score: float = 0, max_score: float = 200) -> List[Location]:
        return [node for node in self.nodes.values() if min_score <= node.score <= max_score]
    
    def get_valid_locations(self) -> List[Location]:
        return [loc for loc in self.nodes.values() if self._is_valid_planting_location(loc)]
    
    def build_from_locations(self, locations: List[Dict[str, Any]]) -> 'CityGraph':
        self.nodes = {}
        for i, data in enumerate(locations):
            node_id = f"node_{i:04d}"
            lat, lon = data['location']
            location = Location(
                node_id=node_id, latitude=lat, longitude=lon,
                pollution=data.get('pollution', 50),
                temperature=data.get('temperature', 25),
                land_type=data.get('land_type', 'empty')
            )
            if data.get('has_tree'):
                location.planted_trees = 1
            location.is_factory = data.get('is_factory', False)
            location.computed_benefit = data.get('computed_benefit', 0)
            self.nodes[node_id] = location
        self._build_edges()
        return self
    
    def build_from_real_data(self, pollution_data: List[Dict], temperature_data: List[Dict]) -> None:
        self.nodes = {}
        all_locations = {}
        
        for item in pollution_data:
            key = f"{item['location'][0]:.4f}_{item['location'][1]:.4f}"
            all_locations[key] = {
                'location': item['location'], 'pollution': item['pollution'],
                'temperature': 25.0, 'land_type': item.get('land_type', 'empty'),
                'has_tree': False, 'is_factory': False, 'source': item.get('source', 'unknown')
            }
        
        for item in temperature_data:
            key = f"{item['location'][0]:.4f}_{item['location'][1]:.4f}"
            if key in all_locations:
                all_locations[key]['temperature'] = item.get('temperature', 25.0)
            else:
                all_locations[key] = {
                    'location': item['location'], 'pollution': 50.0,
                    'temperature': item.get('temperature', 25.0),
                    'land_type': item.get('land_type', 'empty'),
                    'has_tree': False, 'is_factory': False, 'source': item.get('source', 'unknown')
                }
        
        for i, (key, data) in enumerate(all_locations.items()):
            node_id = f"node_{i:04d}"
            lat, lon = data['location']
            location = Location(
                node_id=node_id, latitude=lat, longitude=lon,
                pollution=data['pollution'], temperature=data['temperature'],
                land_type=data['land_type']
            )
            if data.get('has_tree'):
                location.planted_trees = 1
            location.is_factory = data.get('is_factory', False)
            location.computed_benefit = data.get('computed_benefit', 0)
            self.nodes[node_id] = location
        
        self._build_edges()
    
    def _build_edges(self, max_distance: Optional[int] = None) -> None:
        if max_distance is None:
            max_distance = self.DEFAULT_EDGE_MAX_DISTANCE
        
        if len(self.nodes) > 1000:
            self._build_edges_grid_based(min(max_distance, 1000))
        else:
            self._build_edges_bruteforce(max_distance)
    
    def _build_edges_bruteforce(self, max_distance: int) -> None:
        self.edges = {node_id: [] for node_id in self.nodes}
        node_list = list(self.nodes.items())
        for i in range(len(node_list)):
            id1, loc1 = node_list[i]
            pos1 = loc1.get_location()
            for j in range(i + 1, len(node_list)):
                id2, loc2 = node_list[j]
                pos2 = loc2.get_location()
                if self.calculate_distance(pos1, pos2) <= max_distance:
                    self.edges[id1].append(id2)
                    self.edges[id2].append(id1)
    
    def _build_edges_grid_based(self, max_distance: int) -> None:
        self.edges = {node_id: [] for node_id in self.nodes}
        grid_size_deg = max(max_distance / 111320, 0.001)
        buckets = {}
        
        for node_id, location in self.nodes.items():
            key = (int(location.latitude / grid_size_deg), int(location.longitude / grid_size_deg))
            buckets.setdefault(key, []).append((node_id, location))
        
        for (gx, gy), points in buckets.items():
            for nx in (gx - 1, gx, gx + 1):
                for ny in (gy - 1, gy, gy + 1):
                    for id1, loc1 in points:
                        pos1 = loc1.get_location()
                        for id2, loc2 in buckets.get((nx, ny), []):
                            if id1 != id2 and id2 not in self.edges.get(id1, []):
                                if self.calculate_distance(pos1, loc2.get_location()) <= max_distance:
                                    self.edges.setdefault(id1, []).append(id2)
                                    self.edges.setdefault(id2, []).append(id1)
    
    def get_node(self, node_id: str) -> Optional[Location]:
        return self.nodes.get(node_id)
    
    def get_location(self, node_id: str) -> Optional[Tuple[float, float]]:
        node = self.get_node(node_id)
        return node.get_location() if node else None
    
    def get_neighbors(self, node_id: str) -> List[str]:
        return self.edges.get(node_id, [])
    
    def get_state(self) -> Dict[str, Any]:
        state = {}
        for node_id, location in self.nodes.items():
            state[node_id] = {
                'location': location.get_location(), 'pollution': location.pollution,
                'temperature': location.temperature, 'land_type': location.land_type,
                'has_tree': location.has_tree, 'is_factory': location.is_factory,
                'score': location.score, 'tree_capacity': location.tree_capacity,
                'planted_trees': location.planted_trees
            }
        return state
    
    @staticmethod
    def calculate_distance(loc1: Tuple[float, float], loc2: Tuple[float, float]) -> float:
        lat1, lon1 = loc1
        lat2, lon2 = loc2
        R = 6371000
        phi1, phi2 = math.radians(lat1), math.radians(lat2)
        dphi, dlambda = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
        a = math.sin(dphi/2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda/2)**2
        return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    def get_plantable_locations(self) -> List[str]:
        return [node_id for node_id, loc in self.nodes.items() if self._is_valid_planting_location(loc)]
    
    def get_plantable_locations_with_scores(self) -> List[Dict[str, Any]]:
        plantable = []
        for node_id, loc in self.nodes.items():
            if self._is_valid_planting_location(loc):
                plantable.append({
                    'node_id': node_id, 'score': loc.score,
                    'computed_benefit': loc.computed_benefit,
                    'tree_capacity': loc.tree_capacity, 'planted_trees': loc.planted_trees,
                    'pollution': loc.pollution, 'temperature': loc.temperature,
                    'land_type': loc.land_type
                })
        plantable.sort(key=lambda x: x.get('computed_benefit', x['score']), reverse=True)
        return plantable
    
    def plant_tree(self, node_id: str, effect: float = 1.0, propagate_effect: bool = True) -> bool:
        location = self.nodes.get(node_id)
        if not location or not self._is_valid_planting_location(location) or not location.can_plant_more():
            return False
        success = location.plant_tree(effect)
        if success and propagate_effect:
            self._apply_tree_effect(node_id, effect)
        return success
    
    def can_plant_more_trees(self, node_id: str) -> bool:
        location = self.nodes.get(node_id)
        return location.can_plant_more() if location else False
    
    def _apply_tree_effect(self, tree_node: str, effect: float = 1.0,
                          effect_distance: Optional[int] = None) -> None:
        if effect_distance is None:
            effect_distance = self.DEFAULT_TREE_EFFECT_DISTANCE
        tree_loc = self.nodes[tree_node].get_location()
        for node_id, location in self.nodes.items():
            if node_id == tree_node:
                continue
            dist = self.calculate_distance(tree_loc, location.get_location())
            if dist <= effect_distance:
                factor = effect * (1 - dist / effect_distance)
                location.pollution = max(0, location.pollution * (1 - 0.15 * factor))
                location.temperature = max(0, location.temperature - factor)
                location.update_score()
    
    def build_factory(self, node_id: str, effect: float = 1.0, propagate_effect: bool = True) -> bool:
        location = self.nodes.get(node_id)
        if not location:
            return False
        location.add_factory(effect)
        if propagate_effect:
            self._apply_factory_effect(node_id, effect)
        return True
    
    def remove_factory(self, node_id: str, revert_effect: bool = True) -> bool:
        location = self.nodes.get(node_id)
        if not location or not location.is_factory:
            return False
        location.remove_factory()
        if revert_effect:
            self._revert_factory_effect(node_id)
        return True
    
    def _apply_factory_effect(self, factory_node: str, effect: float = 1.0,
                             effect_distance: Optional[int] = None) -> None:
        if effect_distance is None:
            effect_distance = self.DEFAULT_FACTORY_EFFECT_DISTANCE
        factory_loc = self.nodes[factory_node].get_location()
        for node_id, location in self.nodes.items():
            if node_id == factory_node:
                continue
            dist = self.calculate_distance(factory_loc, location.get_location())
            if dist <= effect_distance:
                factor = effect * (1 - dist / effect_distance)
                location.pollution += 5 * factor
                location.temperature += 1.0 * factor
                location.update_score()
    
    def _revert_factory_effect(self, factory_node: str, effect_distance: Optional[int] = None) -> None:
        if effect_distance is None:
            effect_distance = self.DEFAULT_FACTORY_EFFECT_DISTANCE
        factory_loc = self.nodes[factory_node].get_location()
        for node_id, location in self.nodes.items():
            if node_id == factory_node:
                continue
            dist = self.calculate_distance(factory_loc, location.get_location())
            if dist <= effect_distance:
                factor = 1 - dist / effect_distance
                location.pollution = max(0, location.pollution - 5 * factor)
                location.temperature = max(-20, location.temperature - 1.0 * factor)
                location.update_score()
    
    def integrate_dataloader_data(self, processed_data: List[Dict[str, Any]], tolerance: float = 0.0001) -> int:
        updated = 0
        for point in processed_data:
            lat, lon = point['location']
            for loc in self.nodes.values():
                if abs(loc.latitude - lat) <= tolerance and abs(loc.longitude - lon) <= tolerance:
                    loc.computed_benefit = point.get('computed_benefit', loc.score)
                    loc.pollution = point.get('pollution', loc.pollution)
                    loc.temperature = point.get('temperature', loc.temperature)
                    loc.land_type = point.get('land_type', loc.land_type)
                    loc.update_score()
                    updated += 1
                    break
        return updated
    
    def update_all_scores(self) -> None:
        for loc in self.nodes.values():
            loc.update_from_environment()
    
    def get_statistics(self) -> Dict[str, Any]:
        if not self.nodes:
            return {'error': 'No nodes in graph'}
        
        scores = [node.score for node in self.nodes.values()]
        capacities = [node.tree_capacity for node in self.nodes.values()]
        plantable = self.get_plantable_locations_with_scores()
        valid_locations = self.get_valid_locations()
        
        return {
            'total_nodes': len(self.nodes),
            'total_edges': sum(len(e) for e in self.edges.values()) // 2,
            'avg_score': sum(scores) / len(scores),
            'max_score': max(scores),
            'min_score': min(scores),
            'total_tree_capacity': sum(capacities),
            'total_trees_planted': sum(node.planted_trees for node in self.nodes.values()),
            'plantable_locations_count': len(plantable),
            'valid_locations_count': len(valid_locations),
            'factories_count': sum(1 for node in self.nodes.values() if node.is_factory),
            'best_locations': [{'id': loc.node_id, 'score': loc.score, 'benefit': loc.computed_benefit}
                               for loc in self.get_best_locations(5)]
        }
    
    def get_network_summary(self) -> Dict[str, Any]:
        if not self.nodes:
            return {'error': 'No nodes in graph'}
        
        n = len(self.nodes)
        m = sum(len(e) for e in self.edges.values()) // 2
        avg_degree = (2 * m) / n if n > 0 else 0
        max_edges = n * (n - 1) / 2
        density = m / max_edges if max_edges > 0 else 0
        
        visited = set()
        components = []
        for node_id in self.nodes:
            if node_id not in visited:
                component = []
                queue = [node_id]
                visited.add(node_id)
                while queue:
                    curr = queue.pop(0)
                    component.append(curr)
                    for nb in self.edges.get(curr, []):
                        if nb not in visited:
                            visited.add(nb)
                            queue.append(nb)
                components.append(component)
        
        return {
            'num_nodes': n, 'num_edges': m, 'avg_degree': avg_degree,
            'graph_density': density, 'num_components': len(components),
            'largest_component_size': max(len(c) for c in components) if components else 0,
            'is_connected': len(components) == 1
        }
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name, 'center': (self.center_lat, self.center_lon),
            'nodes': {nid: loc.to_dict() for nid, loc in self.nodes.items()},
            'edges': self.edges, 'statistics': self.get_statistics()
        }