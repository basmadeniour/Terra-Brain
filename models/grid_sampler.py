import math
import csv
import random
from typing import List, Tuple, Optional, Dict, Any
from shapely.geometry import Point, Polygon


class GridSampler:

    METERS_PER_DEGREE_LAT = 111320
    
    def __init__(self, spacing_meters: float = 100, use_covers: bool = True, tolerance: float = 1e-7):
        self.spacing_meters = spacing_meters
        self.use_covers = use_covers
        self.tolerance = tolerance
        self._last_bounds = None
        self._last_points = None

    @staticmethod
    def meters_to_degrees(meters: float, latitude: float) -> Tuple[float, float]:
        lat_deg = meters / GridSampler.METERS_PER_DEGREE_LAT
        meters_per_deg_lon = GridSampler.METERS_PER_DEGREE_LAT * math.cos(math.radians(latitude))
        lon_deg = meters / max(meters_per_deg_lon, 1)
        return lat_deg, lon_deg

    @staticmethod
    def degrees_to_meters(lat_deg: float, lon_deg: float, latitude: float) -> Tuple[float, float]:
        lat_m = lat_deg * GridSampler.METERS_PER_DEGREE_LAT
        lon_m = lon_deg * GridSampler.METERS_PER_DEGREE_LAT * math.cos(math.radians(latitude))
        return lat_m, lon_m

    @staticmethod
    def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        R = 6371000
        lat1_r, lon1_r, lat2_r, lon2_r = map(math.radians, [lat1, lon1, lat2, lon2])
        dlat, dlon = lat2_r - lat1_r, lon2_r - lon1_r
        a = math.sin(dlat/2)**2 + math.cos(lat1_r) * math.cos(lat2_r) * math.sin(dlon/2)**2
        return R * 2 * math.asin(math.sqrt(a))

    def _point_in_polygon(self, polygon: Polygon, lon: float, lat: float) -> bool:
        point = Point(lon, lat)
        if self.use_covers:
            if polygon.covers(point):
                return True
        else:
            if polygon.contains(point):
                return True
        if polygon.buffer(self.tolerance).contains(point):
            return True
        if polygon.distance(point) <= self.tolerance:
            return True
        return False

    def generate_grid_points(self, polygon_coords: List[Tuple[float, float]], 
                            include_boundary: bool = True) -> List[Tuple[float, float]]:
        if not polygon_coords or len(polygon_coords) < 3:
            return []
        
        polygon = Polygon([(lon, lat) for lat, lon in polygon_coords])
        if not polygon.is_valid:
            polygon = polygon.buffer(0)
            if not polygon.is_valid:
                return []
        
        min_lon, min_lat, max_lon, max_lat = polygon.bounds
        lat_range, lon_range = max_lat - min_lat, max_lon - min_lon
        expansion = max(lat_range, lon_range) * 0.001
        
        min_lat_exp = min_lat - expansion
        max_lat_exp = max_lat + expansion
        min_lon_exp = min_lon - expansion
        max_lon_exp = max_lon + expansion
        
        center_lat = (min_lat + max_lat) / 2
        lat_step, lon_step = self.meters_to_degrees(self.spacing_meters, center_lat)
        min_step = 0.000009
        lat_step, lon_step = max(lat_step, min_step), max(lon_step, min_step)
        
        points = []
        lat = min_lat_exp
        while lat <= max_lat_exp + self.tolerance:
            lon = min_lon_exp
            while lon <= max_lon_exp + self.tolerance:
                if self._point_in_polygon(polygon, lon, lat):
                    points.append((lat, lon))
                lon += lon_step
            lat += lat_step
        
        if points:
            unique = {}
            for lat, lon in points:
                key = (round(lat, 7), round(lon, 7))
                if key not in unique:
                    unique[key] = (lat, lon)
            points = list(unique.values())
        
        self._last_bounds = (min_lat, max_lat, min_lon, max_lon)
        self._last_points = points
        return points

    def generate_grid_from_bounds(self, min_lat: float, max_lat: float,
                                   min_lon: float, max_lon: float,
                                   center_lat: float = None) -> List[Tuple[float, float]]:
        if center_lat is None:
            center_lat = (min_lat + max_lat) / 2
        
        lat_step, lon_step = self.meters_to_degrees(self.spacing_meters, center_lat)
        min_step = 0.000009
        lat_step, lon_step = max(lat_step, min_step), max(lon_step, min_step)
        
        points = []
        lat = min_lat
        while lat <= max_lat + self.tolerance:
            lon = min_lon
            while lon <= max_lon + self.tolerance:
                points.append((lat, lon))
                lon += lon_step
            lat += lat_step
        return points

    def generate_optimized_grid(self, polygon_coords: List[Tuple[float, float]],
                                 buffer_meters: float = 0,
                                 include_boundary: bool = True) -> List[Tuple[float, float]]:
        if not polygon_coords or len(polygon_coords) < 3:
            return []
        
        polygon = Polygon([(lon, lat) for lat, lon in polygon_coords])
        
        if buffer_meters != 0:
            center_lat = polygon.centroid.y
            buffer_deg = max(self.meters_to_degrees(abs(buffer_meters), center_lat))
            polygon = polygon.buffer(buffer_deg if buffer_meters > 0 else -buffer_deg)
        
        min_lon, min_lat, max_lon, max_lat = polygon.bounds
        lat_range, lon_range = max_lat - min_lat, max_lon - min_lon
        expansion = max(lat_range, lon_range) * 0.001
        
        min_lat_exp, max_lat_exp = min_lat - expansion, max_lat + expansion
        min_lon_exp, max_lon_exp = min_lon - expansion, max_lon + expansion
        
        center_lat = (min_lat + max_lat) / 2
        lat_step, lon_step = self.meters_to_degrees(self.spacing_meters, center_lat)
        min_step = 0.000009
        lat_step, lon_step = max(lat_step, min_step), max(lon_step, min_step)
        
        points = []
        lat = min_lat_exp
        while lat <= max_lat_exp + self.tolerance:
            lat_intersects = False
            lon = min_lon_exp
            while lon <= max_lon_exp + self.tolerance:
                if self._point_in_polygon(polygon, lon, lat):
                    lat_intersects = True
                    break
                lon += lon_step
            
            if lat_intersects:
                lon = min_lon_exp
                while lon <= max_lon_exp + self.tolerance:
                    if self._point_in_polygon(polygon, lon, lat):
                        points.append((lat, lon))
                    lon += lon_step
            lat += lat_step
        
        self._last_bounds = (min_lat, max_lat, min_lon, max_lon)
        self._last_points = points
        return points

    def generate_dense_grid(self, polygon_coords: List[Tuple[float, float]],
                            target_points: int = 100) -> List[Tuple[float, float]]:
        if not polygon_coords or len(polygon_coords) < 3:
            return []
        
        polygon = Polygon([(lon, lat) for lat, lon in polygon_coords])
        area_km2 = polygon.area * 111.32 * 111.32
        points_per_km2 = target_points / area_km2 if area_km2 > 0 else 10
        spacing_km = math.sqrt(1 / points_per_km2) if points_per_km2 > 0 else 0.1
        self.spacing_meters = max(10, min(500, spacing_km * 1000))
        return self.generate_grid_points(polygon_coords)

    def get_grid_statistics(self, points: List[Tuple[float, float]]) -> Dict[str, Any]:
        if not points:
            return {'count': 0, 'error': 'No points'}
        
        lats, lons = [p[0] for p in points], [p[1] for p in points]
        lat_range, lon_range = max(lats) - min(lats), max(lons) - min(lons)
        center_lat = (min(lats) + max(lats)) / 2
        lat_m = lat_range * self.METERS_PER_DEGREE_LAT
        lon_m = lon_range * self.METERS_PER_DEGREE_LAT * math.cos(math.radians(center_lat))
        area_km2 = (lat_m * lon_m) / 1_000_000
        density = len(points) / area_km2 if area_km2 > 0 else 0
        
        if len(points) > 1:
            sample = points[:100] if len(points) > 100 else points
            total = 0
            for i in range(len(sample) - 1):
                total += self.haversine_distance(sample[i][0], sample[i][1], sample[i+1][0], sample[i+1][1])
            avg_spacing = total / (len(sample) - 1)
        else:
            avg_spacing = self.spacing_meters
        
        return {
            'count': len(points), 'min_lat': min(lats), 'max_lat': max(lats),
            'min_lon': min(lons), 'max_lon': max(lons), 'area_km2': area_km2,
            'density_per_km2': density, 'spacing_meters': self.spacing_meters,
            'actual_avg_spacing_meters': avg_spacing,
            'estimated_km_between_points': self.spacing_meters / 1000
        }

    def to_csv(self, points: List[Tuple[float, float]], filename: str):
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['latitude', 'longitude'])
            writer.writerows(points)
        print(f"Saved {len(points)} points to {filename}")

    def to_geojson(self, points: List[Tuple[float, float]], filename: str):
        import json
        features = [{
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [lon, lat]},
            "properties": {"id": i, "type": "grid_point"}
        } for i, (lat, lon) in enumerate(points)]
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump({"type": "FeatureCollection", "features": features}, f, indent=2)
        print(f"Saved {len(points)} points to {filename}")

    def get_sample_points(self, points: List[Tuple[float, float]], 
                          num_samples: int = 10,
                          method: str = 'random') -> List[Tuple[float, float]]:
        if len(points) <= num_samples:
            return points
        if method == 'uniform':
            step = len(points) // num_samples
            return [points[i] for i in range(0, len(points), step)][:num_samples]
        return random.sample(points, num_samples)

    def print_summary(self, points: List[Tuple[float, float]]):
        stats = self.get_grid_statistics(points)
        if 'error' in stats:
            print(f"\n{stats['error']}")
            return
        print(f"\n{'='*60}\nGRID SAMPLER SUMMARY\n{'='*60}")
        print(f"Total points:        {stats['count']}")
        print(f"Target spacing:      {stats['spacing_meters']}m (~{stats['estimated_km_between_points']:.2f}km)")
        print(f"Actual spacing:      {stats['actual_avg_spacing_meters']:.1f}m")
        print(f"Latitude bounds:     {stats['min_lat']:.4f} -> {stats['max_lat']:.4f}")
        print(f"Longitude bounds:    {stats['min_lon']:.4f} -> {stats['max_lon']:.4f}")
        print(f"Estimated area:      {stats['area_km2']:.2f} km²")
        print(f"Point density:       {stats['density_per_km2']:.1f} points/km²")
        print("="*60)