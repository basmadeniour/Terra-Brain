import tkinter as tk
from ui.main_window import MainWindow
from data.real_data_fetcher import RealDataFetcherFast
from models.city_graph import CityGraph
from models.grid_sampler import GridSampler
from models.location import Location
from problem.state import State
from optimization.solvers import CSPOptimizer, HybridSolver
import warnings
import time
import requests
import math
from tkinter import messagebox
from shapely.geometry import Polygon

warnings.filterwarnings('ignore')


class UrbanGreenPlanner:
    
    def __init__(self):
        self.city_graph = None
        self.data_fetcher = RealDataFetcherFast(verbose=False, tile_size_deg=0.1, use_h3=False)
        self.cities_cache = {}
        self.main_window = None
        self.state = None
        self.optimizer = None
        self.last_decisions = None
        
    def search_city_online(self, city_name):
        try:
            url = "https://nominatim.openstreetmap.org/search"
            params = {"q": city_name, "format": "json", "limit": 5, "addressdetails": 1, "featuretype": "city|town|village"}
            headers = {'User-Agent': 'UrbanGreenPlanner/1.0', 'Accept-Language': 'en'}
            
            response = requests.get(url, params=params, headers=headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if not data:
                    return []
                
                results = []
                for item in data:
                    lat, lon = float(item["lat"]), float(item["lon"])
                    display_name = item.get("display_name", "Unknown")
                    addr = item.get("address", {})
                    city = addr.get("city") or addr.get("town") or addr.get("village") or display_name.split(",")[0]
                    country = addr.get("country", "")
                    results.append({
                        "name": f"{city}, {country}" if country else city,
                        "full_name": display_name, "lat": lat, "lon": lon,
                        "city": city, "country": country
                    })
                return results
        except Exception as e:
            print(f"Search error: {e}")
        return []
    
    def update_map_center(self, lat, lon, city_name="Selected Area"):
        print(f"\nUpdating map center to: {city_name} ({lat:.4f}, {lon:.4f})")
        if self.city_graph is None:
            self.city_graph = CityGraph(city_name)
        self.city_graph.center_lat, self.city_graph.center_lon = lat, lon
        if self.main_window and hasattr(self.main_window, 'update_map_center'):
            self.main_window.update_map_center(lat, lon)
        else:
            self.show_map_with_center(lat, lon, city_name)
    
    def show_map_with_center(self, lat, lon, city_name="Selected Area"):
        print(f"\n{'='*70}")
        print(f"Opening map centered at: {city_name} ({lat:.4f}, {lon:.4f})")
        print(f"{'='*70}")
        print("\nINSTRUCTIONS:")
        print("   1. Use the drawing tools on the map")
        print("   2. Draw a polygon around the area you want to analyze")
        print("   3. The system will fetch data ONLY inside your polygon")
        print("   4. Then you can run AI optimization algorithms\n")
        
        self.city_graph = CityGraph(city_name)
        self.city_graph.center_lat, self.city_graph.center_lon = lat, lon
        self.run_ui()
    
    def initialize_with_polygon_streaming(self, polygon_coords, callback=None):
        print(f"\n{'='*70}")
        print(f"PROCESSING POLYGON with {len(polygon_coords)} points")
        print(f"{'='*70}")
        
        if len(polygon_coords) < 3:
            print("Invalid polygon: need at least 3 points")
            return False
        
        from shapely.geometry import Polygon as ShapelyPolygon
        polygon = ShapelyPolygon([(lon, lat) for lat, lon in polygon_coords])
        
        area = self._calculate_polygon_area_km2(polygon_coords)
        if area > 15:
            print(f"Polygon area too large: {area:.1f} km (max: 15 km)")
            return False
        
        print(f"Polygon area: {area:.2f} km")
        print(f"\nGenerating grid points...")
        
        sampler = GridSampler(spacing_meters=100, use_covers=True)
        points = sampler.generate_grid_points(polygon_coords)
        print(f"   Generated {len(points)} grid points")
        
        if len(points) == 0:
            print("No points generated inside polygon")
            return False
        
        print(f"\nFetching environmental data...")
        try:
            area_data = self.data_fetcher.fetch_area_data_fast(polygon, num_tiles=3)
            print(f"   Temperature: {area_data['temperature']:.1f}C")
            print(f"   Pollution: {area_data['pollution']:.1f} ug/m3")
        except Exception as e:
            print(f"Error fetching area data: {e}")
            area_data = {'temperature': 25.0, 'pollution': 50.0,
                        'center': (polygon.centroid.y, polygon.centroid.x),
                        'bounds': polygon.bounds}
        
        self.city_graph = CityGraph(f"Polygon Area ({len(points)} points)")
        
        points_dict = [{'location': (p[0], p[1])} for p in points]
        enhanced = self.data_fetcher.distribute_area_data_to_points(points_dict, area_data, add_variation=True, variation_std=2.0)
        
        for i, data in enumerate(enhanced):
            nid = f"node_{i:04d}"
            lat, lon = data['location']
            loc = Location(nid, lat, lon,
                          pollution=data.get('pollution', 50),
                          temperature=data.get('temperature', 25),
                          land_type=data.get('land_type', 'empty'))
            loc.computed_benefit = data.get('computed_benefit', 0)
            self.city_graph.nodes[nid] = loc
            
            if callback:
                callback({'node_id': nid, 'location': (lat, lon),
                         'pollution': loc.pollution, 'temperature': loc.temperature,
                         'land_type': loc.land_type, 'is_plantable': loc.is_plantable(),
                         'score': loc.score, 'has_tree': loc.has_tree,
                         'refine_level': 0, 'progress': (i + 1) / len(enhanced) * 100})
            
            if i % 5 == 0:
                time.sleep(0.01)
        
        print(f"\nBuilding graph edges...")
        self.city_graph._build_edges(max_distance=500)
        self.state = State(self.city_graph)
        
        stats = self.city_graph.get_statistics()
        print(f"\nGraph Statistics:")
        print(f"   Total nodes: {stats['total_nodes']}")
        print(f"   Plantable: {stats['plantable_locations_count']}")
        print(f"   Avg score: {stats['avg_score']:.1f}")
        
        return True
    
    def _calculate_polygon_area_km2(self, coords):
        if len(coords) < 3:
            return 0
        R, points = 6371, []
        for lat, lon in coords:
            points.append((math.radians(lat), math.radians(lon)))
        area = 0
        for i in range(len(points)):
            j = (i + 1) % len(points)
            lat1, lon1 = points[i]
            lat2, lon2 = points[j]
            area += (lon2 - lon1) * (2 + math.sin(lat1) + math.sin(lat2))
        return abs(area * R * R / 2)
    
    def auto_select_algorithm(self):
        if self.state is None:
            return 'greedy'
        n = len(self.state.get_plantable_locations())
        if n <= 25:
            return 'backtracking'
        elif n <= 150:
            return 'genetic'
        else:
            return 'hill_climbing'
    
    def run_optimization_auto(self, max_trees=100, min_distance=10):
        if self.state is None or len(self.state.locations) == 0:
            print("No state available. Please draw a polygon first.")
            return None
        
        method = self.auto_select_algorithm()
        n_vars = len(self.state.get_plantable_locations())
        print(f"Auto-selected: {method.upper()} for {n_vars} locations")
        return self.run_optimization(method=method, max_trees=max_trees, min_distance=min_distance)
    
    def run_optimization(self, method='hybrid', max_trees=100, min_distance=10,
                         population_size=50, generations=50, mutation_rate=0.1):
        if self.state is None or len(self.state.locations) == 0:
            print("No state available. Please draw a polygon first.")
            return None
        
        names = {'greedy': 'Greedy Search', 'backtracking': 'Backtracking CSP',
                 'hill_climbing': 'Hill Climbing', 'genetic': 'Genetic Algorithm',
                 'hybrid': 'Hybrid Solver'}
        
        print(f"\n{'='*50}")
        print(f"Running AI Optimization: {names.get(method, method.upper())}")
        print(f"{'='*50}")
        print(f"Variables: {len(self.state.locations)} locations")
        print(f"Max trees: {max_trees}")
        print(f"Min distance: {min_distance}m")
        print(f"{'='*50}")
        
        start = time.time()
        
        if method == 'hybrid':
            self.optimizer = HybridSolver(max_trees=max_trees, min_distance=min_distance)
        else:
            self.optimizer = CSPOptimizer(method=method, max_trees=max_trees, min_distance=min_distance)
        
        decisions = self.optimizer.solve(self.state)
        elapsed = time.time() - start
        
        if decisions:
            trees = sum(1 for v in decisions.values() if v == 1)
            score = self._evaluate_decisions(decisions)
            print(f"\nSolution found in {elapsed:.3f}s")
            print(f"   Trees planted: {trees}")
            print(f"   Objective score: {score:.1f}")
            
            stats = {}
            try:
                if hasattr(self.optimizer, 'get_statistics'):
                    stats = self.optimizer.get_statistics()
                elif hasattr(self.optimizer, 'stats'):
                    stats = self.optimizer.stats
            except AttributeError:
                pass
            
            if stats:
                for k in ['nodes_explored', 'pruned', 'generations', 'iterations']:
                    if k in stats:
                        print(f"   {k.replace('_',' ').title()}: {stats[k]}")
            
            self.last_decisions = decisions
            return decisions
        else:
            print(f"\nNo solution found in {elapsed:.3f}s")
            return None
    
    def _evaluate_decisions(self, decisions):
        total = 0.0
        for loc in self.state.locations:
            if decisions.get(loc.node_id, 0) == 1:
                p = max(0, loc.pollution * 0.85)
                t = max(0, loc.temperature - 2)
                p_norm = min(1.0, p / 200.0)
                t_norm = min(1.0, abs(t - 22.0) / 20.0)
            else:
                p_norm = min(1.0, loc.pollution / 200.0)
                t_norm = min(1.0, abs(loc.temperature - 22.0) / 20.0)
            
            env = 100 * (1 - (0.6 * p_norm + 0.4 * t_norm))
            bonus = {'park': 10, 'forest': 15, 'agricultural': 10, 'grass': 5,
                     'empty': 0, 'residential': -5, 'industrial': -20,
                     'building': -30, 'road': -30}.get(loc.land_type, 0)
            total += max(0, min(100, env + bonus))
        return total
    
    def apply_decisions_to_visualization(self, decisions):
        if not decisions:
            return []
        selected = [nid for nid, val in decisions.items() if val == 1]
        print(f"Selected {len(selected)} locations for visualization")
        return selected
    
    def reset_state(self):
        if self.city_graph:
            self.state = State(self.city_graph)
            print(f"State reset with {len(self.state.locations)} locations")
    
    def run_ui(self):
        if self.city_graph is None:
            print("\nNo graph initialized. Please select a city or area first.")
            return
        
        if self.main_window is not None:
            print("\nUI already running, updating graph...")
            self.main_window.update_graph(self.city_graph)
            return
        
        print(f"\nStarting user interface...")
        print(f"   Locations: {len(self.city_graph.nodes)}")
        valid = len(self.city_graph.get_valid_locations()) if self.city_graph.nodes else 0
        print(f"   Valid locations: {valid}")
        
        root = tk.Tk()
        self.main_window = MainWindow(root, self.city_graph, planner=self)
        root.mainloop()
    
    def run(self, city=None):
        print(f"\n{'='*70}")
        print("TERRA BRAIN - SMART TREE PLACEMENT SYSTEM")
        print(f"{'='*70}")
        print("\nSMART FEATURES:")
        print("   - Automatically chooses best strategy for your area")
        print("   - Real-time distance calculation between points")
        print("   - Refine points for higher resolution")
        print(f"{'='*70}\n")
        print("HOW TO USE:")
        print("   1. Search for a city using the search bar")
        print("   2. Click the polygon drawing tool on the map")
        print("   3. Draw a polygon around your area of interest")
        print("   4. Enter how many trees you want to plant")
        print("   5. Click 'Run Algorithm' - we'll do the rest!")
        print(f"{'='*70}\n")
        
        default_lat, default_lon, default_name = 31.0364, 31.3807, "Mansoura, Egypt"
        
        if city:
            print(f"Searching for city: {city}")
            results = self.search_city_online(city)
            if results:
                r = results[0]
                self.show_map_with_center(r['lat'], r['lon'], r['city'])
            else:
                print(f"City '{city}' not found")
                self.show_map_with_center(default_lat, default_lon, default_name)
        else:
            self.show_map_with_center(default_lat, default_lon, default_name)


if __name__ == "__main__":
    planner = UrbanGreenPlanner()
    planner.run()