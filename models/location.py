import math
from typing import Tuple, Dict, Any, List, Optional


class Location:

    LAND_SCORES = {
        'park': 40, 'forest': 40, 'agricultural': 40,
        'grass': 35, 'meadow': 35, 'garden': 35,
        'empty': 5, 'residential': 10, 'greenfield': 30,
        'rainforest': 35, 'wetland': 25,
        'plantable_empty': 30, 'already_planted': 35,
        'commercial': -20, 'industrial': -50,
        'road': -60, 'building': -70, 'water': -100,
        'barren': -10, 'tundra': 0, 'desert': 0, 'unknown': 0
    }

    AREA_MULTIPLIERS = {
        'park': 1.5, 'forest': 2.0, 'agricultural': 1.8,
        'grass': 1.2, 'meadow': 1.2, 'garden': 1.3,
        'empty': 1.0, 'residential': 0.5, 'greenfield': 1.2,
        'rainforest': 2.0, 'wetland': 1.0,
        'plantable_empty': 1.0, 'already_planted': 1.2,
        'commercial': 0.3, 'industrial': 0.2, 'road': 0.1,
        'building': 0.0, 'water': 0.0, 'barren': 0.3,
        'tundra': 0.1, 'desert': 0.0
    }

    MAX_POLLUTION = 200.0
    IDEAL_TEMPERATURE = 22.0
    POLLUTION_DECAY_RATE = 0.98
    TEMPERATURE_RECOVERY_RATE = 0.05

    def __init__(self, node_id: int, latitude: float, longitude: float,
                 pollution: float = 50.0, temperature: float = 25.0,
                 land_type: str = 'empty', area: float = 2500.0):
        self.node_id = node_id
        self.latitude = latitude
        self.longitude = longitude
        self.pollution = pollution
        self.temperature = temperature
        self.land_type = land_type
        self.area = area
        self.is_factory = False
        self.planted_trees = 0
        self.computed_benefit: float = 0
        self.neighbors: List["Location"] = []
        self.score = self._calculate_score()
        self.tree_capacity = self._calculate_tree_capacity()

    @property
    def has_tree(self) -> bool:
        return self.planted_trees > 0

    def get_location(self) -> Tuple[float, float]:
        return (self.latitude, self.longitude)

    def _calculate_pollution_score(self) -> float:
        norm = min(1.0, self.pollution / self.MAX_POLLUTION)
        return (1 - norm) * 100

    def _calculate_temperature_score(self) -> float:
        diff = abs(self.temperature - self.IDEAL_TEMPERATURE)
        norm = min(1.0, diff / 20.0)
        return (1 - norm) * 100

    def _calculate_land_score(self) -> float:
        base = self.LAND_SCORES.get(self.land_type)
        if base is None:
            base = 5 if self.is_plantable() else -30

        pollution_factor = max(0, 1 - self.pollution / self.MAX_POLLUTION)

        if base >= 0:
            norm_score = (base + 100) / 2
        else:
            norm_score = base / 2

        return max(0, norm_score * pollution_factor)

    def _calculate_score(self) -> float:
        pollution_score = self._calculate_pollution_score()
        temperature_score = self._calculate_temperature_score()
        land_score = self._calculate_land_score()
        score = pollution_score * 0.5 + land_score * 0.3 + temperature_score * 0.2
        return max(0, min(100, score))

    def _calculate_tree_capacity(self) -> int:
        if self.score <= 20:
            return 0

        multiplier = self.AREA_MULTIPLIERS.get(self.land_type, 0.5)
        effective_area = self.area * multiplier

        if self.score > 80:
            spacing = 2.5
        elif self.score > 60:
            spacing = 3.0
        elif self.score > 40:
            spacing = 4.0
        else:
            spacing = 5.0

        trees_per_side = int(math.sqrt(effective_area) / spacing)
        capacity = trees_per_side ** 2
        return max(0, min(capacity, 200))

    def update_score(self) -> float:
        self.score = self._calculate_score()
        self.tree_capacity = self._calculate_tree_capacity()
        return self.score

    def update_from_environment(self) -> float:
        return self.update_score()

    def add_neighbor(self, neighbor: "Location") -> None:
        if neighbor not in self.neighbors and neighbor.node_id != self.node_id:
            self.neighbors.append(neighbor)

    def apply_neighbor_effects(self) -> None:
        for nb in self.neighbors:
            influence = 0.05
            if nb.has_tree:
                reduction = 0.1 * influence * nb.planted_trees
                self.pollution = max(0, self.pollution * (1 - reduction))
                cooling = 0.2 * influence * nb.planted_trees
                self.temperature = max(0, self.temperature - cooling)
            if nb.is_factory:
                self.pollution += 2.0 * influence
                self.temperature += 0.3 * influence
        self.update_score()

    def simulate_step(self, dt: float = 1.0) -> None:
        decay = self.POLLUTION_DECAY_RATE ** (dt / 24)
        self.pollution = max(0, self.pollution * decay)
        diff = self.IDEAL_TEMPERATURE - self.temperature
        recovery = diff * self.TEMPERATURE_RECOVERY_RATE * (dt / 24)
        self.temperature += recovery
        self.apply_neighbor_effects()
        self.update_score()

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.node_id, 'location': self.get_location(),
            'pollution': self.pollution, 'temperature': self.temperature,
            'land_type': self.land_type, 'has_tree': self.has_tree,
            'is_factory': self.is_factory, 'score': self.score,
            'tree_capacity': self.tree_capacity, 'planted_trees': self.planted_trees,
            'computed_benefit': self.computed_benefit, 'area': self.area,
            'neighbors_count': len(self.neighbors)
        }

    def is_plantable(self) -> bool:
        non_plantable = {'building', 'road', 'water', 'commercial',
                         'industrial', 'tundra', 'desert', 'barren'}
        return self.land_type not in non_plantable

    def can_plant_more(self) -> bool:
        return self.planted_trees < self.tree_capacity

    def plant_tree(self, effect: float = 1.0) -> bool:
        if not self.can_plant_more():
            return False

        self.planted_trees += 1
        total = self.planted_trees

        reduction = 1 - math.exp(-0.03 * total * effect)
        self.pollution = max(0, self.pollution * (1 - reduction * 0.5))

        cooling = 1.5 * (1 - math.exp(-0.1 * total)) * effect
        self.temperature = max(0, self.temperature - cooling)

        self.update_score()
        return True

    def remove_tree(self) -> bool:
        if self.planted_trees <= 0:
            return False

        self.planted_trees -= 1

        if self.planted_trees > 0:
            total = self.planted_trees
            reduction = 1 - math.exp(-0.03 * total)
            self.pollution = min(self.MAX_POLLUTION, self.pollution / (1 - reduction * 0.5))
            cooling = 1.5 * (1 - math.exp(-0.1 * total))
            self.temperature = min(50, self.temperature + cooling)

        self.update_score()
        return True

    def add_factory(self, effect: float = 1.0) -> None:
        self.is_factory = True
        increase = 5 + 0.05 * self.pollution
        self.pollution += increase * effect
        self.temperature += 1.0 * effect
        self.update_score()

    def remove_factory(self) -> None:
        self.is_factory = False
        self.pollution = max(0, self.pollution - 5)
        self.temperature = max(-20, min(50, self.temperature - 1.0))
        self.update_score()

    def set_land_type(self, land_type: str) -> None:
        self.land_type = land_type
        self.update_score()

    def get_environmental_summary(self) -> Dict[str, Any]:
        return {
            'pollution': self.pollution,
            'pollution_score': self._calculate_pollution_score(),
            'temperature': self.temperature,
            'temperature_score': self._calculate_temperature_score(),
            'land_score': self._calculate_land_score(),
            'overall_score': self.score,
            'tree_count': self.planted_trees,
            'tree_capacity': self.tree_capacity,
            'has_factory': self.is_factory,
            'neighbors_count': len(self.neighbors)
        }

    def __str__(self) -> str:
        status = "TREE" if self.has_tree else "FACTORY" if self.is_factory else "EMPTY"
        return (f"{status} {self.node_id}: ({self.latitude:.4f}, {self.longitude:.4f}) | "
                f"P:{self.pollution:.1f} T:{self.temperature:.1f}C | "
                f"Score:{self.score:.1f} | Trees:{self.planted_trees}/{self.tree_capacity} | "
                f"Type:{self.land_type} | Area:{self.area:.0f}m2")

    def __repr__(self) -> str:
        return self.__str__()