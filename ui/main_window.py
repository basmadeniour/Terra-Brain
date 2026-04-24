import tkinter as tk
from tkinter import ttk, messagebox
from .map_view_qt import MapView
from .colors import MapColors
import threading
import datetime
import math
from shapely.geometry import Polygon as ShapelyPolygon
from shapely.geometry import Point as ShapelyPoint
from models.grid_sampler import GridSampler
from PIL import Image, ImageTk


class MainWindow:
    
    def __init__(self, root, city_graph, planner=None):
        self.root = root
        self.root.title("TERRA BRAIN - Green Space Planning System")
        self.root.geometry("1400x800")
        self.city_graph = city_graph
        self.planner = planner
        
        self.colors = {
            'bg': '#C1D8C3', 'primary': '#8FB996', 'secondary': '#7DAA87',
            'accent': '#f39c12', 'text': '#1a4d2a', 'text_secondary': '#5a7a4a',
            'button_bg': '#8FB996', 'button_hover': '#7DAA87', 'frame_bg': '#C1D8C3',
            'entry_bg': '#ffffff', 'entry_fg': '#1a4d2a',
        }
        
        self.root.configure(bg=self.colors['bg'])
        self.setup_styles()
        
        self.current_polygon_coords = None
        self.current_points = []
        self.refine_level = 0
        self.average_distance = 0.0
        self.current_city_info = None
        
        self.is_loading = False
        self.total_expected_points = 0
        self.loaded_points_count = 0
        
        self.max_trees = None
        self.refine_button = None
        
        self.setup_layout()
        self.show_welcome_message()
    
    def setup_styles(self):
        style = ttk.Style()
        try:
            style.theme_use('clam')
        except:
            pass
        
        style.configure('TFrame', background=self.colors['bg'])
        style.configure('TLabelframe', background=self.colors['bg'])
        style.configure('TLabelframe.Label', background=self.colors['bg'], 
                       foreground=self.colors['text'], font=('Arial', 10, 'bold'))
        style.configure('TLabel', background=self.colors['bg'], foreground=self.colors['text'])
        style.configure('TButton', background=self.colors['button_bg'], foreground='white',
                       borderwidth=0, focuscolor='none')
        style.map('TButton', background=[('active', self.colors['button_hover']),
                                         ('pressed', self.colors['secondary'])],
                  foreground=[('active', 'white')])
        style.configure('TEntry', fieldbackground=self.colors['entry_bg'],
                       foreground=self.colors['entry_fg'], borderwidth=1)
        style.configure('TProgressbar', background=self.colors['primary'],
                       troughcolor=self.colors['text_secondary'])
        style.configure('TCombobox', fieldbackground=self.colors['entry_bg'],
                       foreground=self.colors['entry_fg'])
    
    def setup_layout(self):
        header = tk.Frame(self.root, bg="#C1D8C3", height=70)
        header.pack(fill=tk.X)
        header.pack_propagate(False)

        left_frame = tk.Frame(header, bg="#C1D8C3")
        left_frame.pack(side=tk.LEFT, padx=15)

        logo_img = Image.open(r"D:\FCIS\3rd\2nd term\Terra Brain\images\logo.png")
        logo_img = logo_img.resize((135, 135))
        self.logo = ImageTk.PhotoImage(logo_img)
        tk.Label(left_frame, image=self.logo, bg="#C1D8C3").pack(side=tk.LEFT)

        tk.Label(left_frame, text="TERRA BRAIN", bg="#C1D8C3", fg="#1a4d2a",
                font=("Arial", 16, "bold"), justify="left").pack(side=tk.LEFT, padx=8)

        center_frame = tk.Frame(header, bg="#C1D8C3")
        center_frame.pack(side=tk.LEFT, expand=True)

        self.search_var = tk.StringVar()
        self.search_entry = tk.Entry(center_frame, textvariable=self.search_var,
                                     width=40, font=("Arial", 11), bd=0, relief="flat")
        self.search_entry.pack(side=tk.LEFT, ipady=6, padx=5)

        tk.Button(center_frame, text="Search City", command=self.search_city,
                  bg="#8FB996", fg="white", font=("Arial", 10, "bold"),
                  bd=0, padx=12, pady=6, cursor="hand2",
                  activebackground="#7DAA87").pack(side=tk.LEFT, padx=5)

        right_frame = tk.Frame(header, bg="#C1D8C3")
        right_frame.pack(side=tk.RIGHT, padx=15)

        tk.Button(right_frame, text="Run Algorithm", command=self.run_selected_algorithm,
                  bg="#8FB996", fg="white", font=("Arial", 10, "bold"),
                  bd=0, padx=15, pady=6, cursor="hand2",
                  activebackground="#7DAA87").pack(side=tk.LEFT, padx=10)

        self.stats_label = tk.Label(right_frame, text="Plantable: 0/0",
                                    bg="#C1D8C3", fg="#1a4d2a", font=("Arial", 11, "bold"))
        self.stats_label.pack(side=tk.LEFT)

        self.distance_label = tk.Label(right_frame, text=" | Avg: -- m",
                                       bg="#C1D8C3", fg="#1a4d2a", font=("Arial", 10))
        self.distance_label.pack(side=tk.LEFT, padx=5)

        self.map_frame = tk.Frame(self.root)
        self.map_frame.pack(fill=tk.BOTH, expand=True)

        self.map_view = MapView(self.map_frame, self.city_graph)
        if hasattr(self.map_view, 'bridge'):
            self.map_view.bridge.polygon_drawn.connect(self.on_polygon_drawn)

        bottom = tk.Frame(self.root, bg="#C1D8C3", height=40)
        bottom.pack(fill=tk.X, side=tk.BOTTOM)

        left_bottom = tk.Frame(bottom, bg="#C1D8C3")
        left_bottom.pack(side=tk.LEFT, padx=10)

        self.refine_button = tk.Button(left_bottom, text="Refine Points",
                                       command=self.refine_points, state="disabled",
                                       bg="#8FB996", fg="white", bd=0, padx=12, pady=5,
                                       activebackground="#7DAA87")
        self.refine_button.pack(side=tk.LEFT)

        self.spacing_info_label = tk.Label(left_bottom, text="", bg="#C1D8C3")
        self.spacing_info_label.pack(side=tk.LEFT, padx=10)

        right_bottom = tk.Frame(bottom, bg="#C1D8C3")
        right_bottom.pack(side=tk.RIGHT, padx=10, fill=tk.X, expand=True)

        self.progress_label = tk.Label(right_bottom, text="Ready", bg="#C1D8C3")
        self.progress_label.pack(side=tk.LEFT, padx=5)

        self.progress_bar = ttk.Progressbar(right_bottom, mode='determinate', length=200)
        self.progress_bar.pack(side=tk.LEFT, fill=tk.X, expand=True)

        control_panel = tk.LabelFrame(self.root, text="Planting Settings",
                                      bg="#C1D8C3", fg="#1a4d2a")
        control_panel.pack(fill=tk.X, padx=10, pady=5)

        row = tk.Frame(control_panel, bg="#C1D8C3")
        row.pack(pady=5)

        tk.Label(row, text="Number of Trees:", bg="#C1D8C3",
                 font=("Arial", 10, "bold")).pack(side=tk.LEFT)
        self.max_trees = tk.Entry(row, width=10)
        self.max_trees.insert(0, "100")
        self.max_trees.pack(side=tk.LEFT, padx=5)
        tk.Label(row, text="(max possible)", bg="#C1D8C3").pack(side=tk.LEFT)

        tk.Label(control_panel, text="Smart Mode: System automatically chooses best strategy",
                 bg="#C1D8C3").pack()
        tk.Label(control_panel, text="Just click 'Run Algorithm' - we'll find the optimal locations!",
                 bg="#C1D8C3").pack()
    
    def sort_points_by_location(self, points):
        return sorted(points, key=lambda p: (p['location'][0], p['location'][1]))
    
    def calculate_average_distance(self, points):
        if len(points) < 2:
            return 0.0
        
        sorted_points = self.sort_points_by_location(points)
        total, count = 0.0, 0
        R = 6371000
        
        for i in range(len(sorted_points) - 1):
            p1, p2 = sorted_points[i], sorted_points[i + 1]
            lat1, lon1 = p1['location'] if isinstance(p1, dict) else p1
            lat2, lon2 = p2['location'] if isinstance(p2, dict) else p2
            
            lat1_r, lat2_r = math.radians(lat1), math.radians(lat2)
            dlat, dlon = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
            a = math.sin(dlat/2)**2 + math.cos(lat1_r) * math.cos(lat2_r) * math.sin(dlon/2)**2
            total += R * 2 * math.asin(math.sqrt(a))
            count += 1
        
        return total / count if count > 0 else 0.0
    
    def update_statistics_display(self):
        if self.is_loading:
            self.stats_label.config(text=f"Loading: {self.loaded_points_count}/{self.total_expected_points}")
        else:
            plantable = sum(1 for p in self.current_points if p.get('is_plantable', False))
            self.stats_label.config(text=f"Plantable: {plantable}/{len(self.current_points)}")
    
    def update_distance_display(self):
        if self.current_points and len(self.current_points) > 1 and not self.is_loading:
            avg = self.calculate_average_distance(self.current_points)
            self.average_distance = avg
            self.distance_label.config(text=f"  |  Avg: {avg/1000:.1f} km" if avg >= 1000 else f"  |  Avg: {avg:.0f} m")
            
            if self.refine_level == 0:
                self.spacing_info_label.config(text=f"(current: {avg:.0f}m)")
            else:
                nxt = avg / 2
                self.spacing_info_label.config(text=f"next: {nxt/1000:.1f}km" if nxt >= 1000 else f"next: {nxt:.0f}m")
        else:
            self.distance_label.config(text="  |  Avg: -- m")
            self.spacing_info_label.config(text="")
    
    def generate_midpoints_grid_based(self, points):
        if len(points) < 2:
            return []
        
        grid, lat_vals, lon_vals = {}, [], []
        for p in points:
            if isinstance(p, dict) and 'location' in p:
                lat, lon = p['location']
                lat_vals.append(lat)
                lon_vals.append(lon)
        
        unique_lats = sorted(set(round(l, 5) for l in lat_vals))
        unique_lons = sorted(set(round(l, 5) for l in lon_vals))
        lat_idx = {lat: i for i, lat in enumerate(unique_lats)}
        lon_idx = {lon: i for i, lon in enumerate(unique_lons)}
        
        for p in points:
            if isinstance(p, dict) and 'location' in p:
                lat, lon = p['location']
                grid[(lat_idx[round(lat, 5)], lon_idx[round(lon, 5)])] = p
        
        new_points, seen = [], set()
        existing = set((round(lat, 6), round(lon, 6)) for p in points
                      if isinstance(p, dict) and 'location' in p for lat, lon in [p['location']])
        
        poly = None
        if self.current_polygon_coords and len(self.current_polygon_coords) >= 3:
            poly = ShapelyPolygon([(lon, lat) for lat, lon in self.current_polygon_coords])
        
        for (i, j), p1 in grid.items():
            for di, dj in [(0, 1), (1, 0), (1, 1)]:
                if (i + di, j + dj) in grid:
                    p2 = grid[(i + di, j + dj)]
                    lat1, lon1 = p1['location']
                    lat2, lon2 = p2['location']
                    mid_lat, mid_lon = (lat1 + lat2) / 2, (lon1 + lon2) / 2
                    key = (round(mid_lat, 6), round(mid_lon, 6))
                    
                    inside = True
                    if poly:
                        point = ShapelyPoint(mid_lon, mid_lat)
                        inside = poly.contains(point) or poly.touches(point)
                    
                    if key not in existing and key not in seen and inside:
                        seen.add(key)
                        new_points.append({'location': (mid_lat, mid_lon), 'refine_level': self.refine_level + 1})
        return new_points
    
    def _fix_land_type(self, land_type: str) -> str:
        plantable_types = ['park', 'forest', 'agricultural', 'grass', 'meadow', 
                           'garden', 'empty', 'residential', 'greenfield', 
                           'plantable_empty', 'already_planted']
        
        if land_type in plantable_types:
            return land_type
        elif land_type in ['building', 'road', 'highway', 'railway']:
            return 'building'
        elif land_type in ['industrial', 'factory', 'manufacturing']:
            return 'industrial'
        elif land_type in ['water', 'river', 'lake', 'sea']:
            return 'water'
        elif land_type in ['desert', 'sand', 'dune']:
            return 'desert'
        elif land_type in ['barren', 'rock', 'gravel']:
            return 'barren'
        else:
            return 'empty'
    
    def search_city(self):
        name = self.search_var.get().strip()
        if not name:
            messagebox.showwarning("Warning", "Please enter a city name")
            return
        
        if self.planner:
            self.set_status("Searching for city...", show_progress=True)
            results = self.planner.search_city_online(name)
            
            if not results:
                self.log(f"City '{name}' not found", "ERROR")
                messagebox.showerror("Error", f"City '{name}' not found")
                self.set_status("Ready", show_progress=False)
                return
            
            if len(results) > 1:
                self.show_city_selection_dialog(results)
            else:
                self.load_city_data(results[0])
        else:
            messagebox.showerror("Error", "Planner not available")
    
    def show_city_selection_dialog(self, results):
        dialog = tk.Toplevel(self.root)
        dialog.title("Select City")
        dialog.geometry("500x400")
        dialog.transient(self.root)
        dialog.grab_set()
        
        tk.Label(dialog, text="Multiple results found. Please select one:",
                font=('Arial', 11)).pack(pady=10)
        
        lb = tk.Listbox(dialog, width=70, height=15)
        lb.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
        for res in results:
            lb.insert(tk.END, res['full_name'])
        
        def on_select():
            sel = lb.curselection()
            if sel:
                self.load_city_data(results[sel[0]])
                dialog.destroy()
        
        tk.Button(dialog, text="Select", command=on_select,
                  bg='#8FB996', fg='white', padx=20).pack(pady=10)
    
    def load_city_data(self, city_info):
        self.log(f"Loading city data: {city_info['name']}", "INFO")
        self.set_status(f"Loading {city_info['name']}...", show_progress=True)
        
        try:
            self.planner.show_map_with_center(city_info['lat'], city_info['lon'], city_info['city'])
            self.city_graph = self.planner.city_graph
            self.map_view.graph = self.city_graph
            
            if hasattr(self.map_view, 'update_map_center'):
                self.map_view.update_map_center(city_info['lat'], city_info['lon'])
            
            if hasattr(self.city_graph, 'center_lat'):
                self.city_graph.center_lat = city_info['lat']
                self.city_graph.center_lon = city_info['lon']
            
            self.current_city_info = city_info
            self.update_statistics_display()
            self.log(f"City {city_info['name']} loaded - draw a polygon to start")
        except Exception as e:
            self.log(f"Error: {str(e)}", "ERROR")
            messagebox.showerror("Error", f"Error during loading: {str(e)}")
        finally:
            self.set_status("Ready", show_progress=False)
    
    def center_map_on_city(self):
        if self.current_city_info and hasattr(self.map_view, 'update_map_center'):
            self.map_view.update_map_center(self.current_city_info['lat'], self.current_city_info['lon'])
            self.log(f"Map centered on: {self.current_city_info['name']}")
    
    def update_graph(self, new_graph):
        self.log(f"Updating graph with {len(new_graph.nodes)} locations")
        self.city_graph = new_graph
        self.map_view.graph = new_graph
        
        self.current_polygon_coords = None
        self.current_points = []
        self.refine_level = 0
        self.is_loading = False
        
        for nid, loc in new_graph.nodes.items():
            lat, lon = loc.get_location()
            self.current_points.append({
                'location': (lat, lon), 'score': loc.score, 'land_type': loc.land_type,
                'is_plantable': loc.is_plantable(), 'pollution': loc.pollution,
                'temperature': loc.temperature, 'has_tree': loc.has_tree, 'refine_level': 0
            })
        
        self.update_distance_display()
        self.update_statistics_display()
        self.map_view.update_map_points(self.prepare_locations_data_for_map(self.current_points))
        self.refine_button.config(state='normal')
        self.log("Graph updated successfully")
    
    def update_map_center(self, lat, lon):
        if hasattr(self.map_view, 'update_center'):
            self.map_view.update_center(lat, lon)
        else:
            self.map_view.init_map()
    
    def sync_current_points_from_graph(self):
        self.log(f"Syncing from graph ({len(self.city_graph.nodes)} nodes)")
        self.current_points = []
        for nid, loc in self.city_graph.nodes.items():
            lat, lon = loc.get_location()
            self.current_points.append({
                'location': (lat, lon), 'score': loc.score, 'land_type': loc.land_type,
                'is_plantable': loc.is_plantable(), 'pollution': loc.pollution,
                'temperature': loc.temperature, 'has_tree': loc.has_tree,
                'refine_level': getattr(loc, 'refine_level', 0)
            })
        self.update_statistics_display()
        self.update_distance_display()
    
    def update_city_graph_from_current_points(self):
        self.log(f"Updating graph from {len(self.current_points)} points")
        if not self.current_points:
            return
        
        self.city_graph.nodes = {}
        for i, p in enumerate(self.current_points):
            nid = f"node_{i:04d}"
            lat, lon = p['location']
            from models.location import Location
            loc = Location(nid, lat, lon, p.get('pollution', 50), p.get('temperature', 25), p.get('land_type', 'empty'))
            loc.score = p.get('score', 0)
            loc.planted_trees = 1 if p.get('has_tree', False) else 0
            loc.refine_level = p.get('refine_level', 0)
            loc.computed_benefit = p.get('score', 0)
            self.city_graph.nodes[nid] = loc
        self.city_graph._build_edges(max_distance=500)
    
    def on_polygon_drawn(self, coords):
        self.log(f"\n{'='*50}\nPOLYGON DRAWN with {len(coords)} points\n{'='*50}")
        
        area = self.calculate_polygon_area_km2(coords)
        if area > 15:
            messagebox.showwarning("Area Too Large", f"Area is {area:.1f} km. Max is 15 km.")
            return
        
        self.set_status("Generating points...", show_progress=True)
        self.progress_bar['value'] = 0
        self.progress_bar['maximum'] = 100
        
        if self.map_view:
            self.map_view.clear_points()
        
        self.current_polygon_coords = coords
        self.current_points = []
        self.refine_level = 0
        self.is_loading = True
        
        def on_point_ready(data):
            self.current_points.append({
                'location': data['location'], 'score': data['score'],
                'land_type': data['land_type'], 'is_plantable': data['is_plantable'],
                'pollution': data['pollution'], 'temperature': data['temperature'],
                'has_tree': data['has_tree'], 'refine_level': data['refine_level']
            })
            self.loaded_points_count = len(self.current_points)
            pct = self.loaded_points_count / self.total_expected_points * 100
            self.progress_bar['value'] = pct
            self.progress_label.configure(text=f"{pct:.0f}%")
            self.update_statistics_display()
            self.root.update_idletasks()
            
            if len(self.current_points) % 5 == 0 or len(self.current_points) == self.total_expected_points:
                self.map_view.update_map_points(self.prepare_locations_data_for_map(self.current_points))
        
        def on_complete(success):
            self.is_loading = False
            if success:
                self.update_distance_display()
                self.update_statistics_display()
                self.refine_button.config(state='normal')
            else:
                messagebox.showerror("Error", "Failed to generate points")
            self.set_status("Ready", show_progress=False)
            self.root.after(500, lambda: self.progress_bar.configure(value=0))
        
        def run():
            try:
                if self.planner:
                    points = GridSampler(spacing_meters=100).generate_grid_points(coords)
                    self.total_expected_points = len(points)
                    success = self.planner.initialize_with_polygon_streaming(coords, callback=on_point_ready)
                    if success and self.planner.city_graph:
                        self.city_graph = self.planner.city_graph
                        self.map_view.graph = self.city_graph
                        self.sync_current_points_from_graph()
                    self.root.after(0, lambda: on_complete(success))
            except Exception as e:
                self.log(f"Error: {e}", "ERROR")
                self.root.after(0, lambda: on_complete(False))
        
        threading.Thread(target=run, daemon=True).start()
    
    def calculate_polygon_area_km2(self, coords):
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
    
    def refine_points(self):
        if not self.current_polygon_coords or not self.current_points:
            self.log("No polygon or points to refine", "WARNING")
            return
        
        self.refine_level += 1
        if self.refine_level > 3:
            self.log("Maximum refine level reached", "INFO")
            self.refine_button.config(state='disabled')
            return
        
        self.set_status(f"Refining to level {self.refine_level}...", show_progress=True)
        new = self.generate_midpoints_grid_based(self.current_points)
        
        if not new:
            self.log("Cannot refine further", "WARNING")
            self.set_status("Ready", show_progress=False)
            return
        
        orig = len(self.current_points)
        for p in new:
            self.current_points.append({
                'location': p['location'], 'score': 0, 'land_type': 'loading',
                'is_plantable': True, 'pollution': 50, 'temperature': 25,
                'has_tree': False, 'refine_level': self.refine_level
            })
        
        processed = 0
        for i in range(orig, len(self.current_points)):
            lat, lon = self.current_points[i]['location']
            processed += 1
            pct = (orig + processed) / len(self.current_points) * 100
            self.progress_bar['value'] = pct
            self.progress_label.configure(text=f"{pct:.0f}%")
            
            try:
                data = self.planner.data_fetcher.fetch_complete_location_data_fast(lat, lon)
                if data:
                    raw_land_type = data.get('land_type', 'empty')
                    fixed_land_type = self._fix_land_type(raw_land_type)
                    data['score'] = self.calculate_location_score(data)
                    self.current_points[i] = {
                        'location': (lat, lon), 'score': data.get('score', 0),
                        'land_type': fixed_land_type,
                        'is_plantable': data.get('is_plantable', True) or fixed_land_type not in ['building', 'road', 'water', 'industrial'],
                        'pollution': data.get('pollution', 50), 'temperature': data.get('temperature', 25),
                        'has_tree': False, 'refine_level': self.refine_level
                    }
                    self.map_view.update_map_points(self.prepare_locations_data_for_map([self.current_points[i]]), append=True)
            except Exception as e:
                self.log(f"Error: {e}", "ERROR")
                self.current_points[i]['land_type'] = 'error'
                self.map_view.update_map_points(self.prepare_locations_data_for_map([self.current_points[i]]), append=True)
        
        self.update_distance_display()
        self.update_statistics_display()
        self.update_city_graph_from_current_points()
        self.set_status("Ready", show_progress=False)
        self.root.after(1000, lambda: self.progress_bar.configure(value=0))
    
    def calculate_location_score(self, data):
        p = data.get('pollution', 50)
        t = data.get('temperature', 25)
        raw_lt = data.get('land_type', 'empty')
        lt = self._fix_land_type(raw_lt)
        
        score = max(0, 100 - p)
        if 15 <= t <= 30:
            score += 20
        elif 10 <= t <= 35:
            score += 10
        else:
            score -= 20
        
        scores = {'park': 40, 'forest': 40, 'agricultural': 40, 'grass': 35,
                  'empty': 30, 'residential': 10, 'commercial': -20, 'industrial': -50,
                  'road': -60, 'building': -70}
        return max(0, score + scores.get(lt, 0))
    
    def prepare_locations_data_for_map(self, locations):
        data = []
        for loc in locations:
            if isinstance(loc, dict) and 'location' in loc:
                lat, lon = loc['location']
                lt = loc.get('land_type', 'unknown')
                plantable = loc.get('is_plantable', True)
                poll = loc.get('pollution', 50)
                temp = loc.get('temperature', 25)
                score = loc.get('score', 0)
                has = loc.get('has_tree', False)
                rl = loc.get('refine_level', 0)
                
                if lt == 'loading':
                    color = '#CCCCCC'
                elif lt == 'error':
                    color = '#FF0000'
                else:
                    color = MapColors.get_land_color(lt, plantable, has)
                
                status = 'Already Planted' if has else ('Plantable' if plantable else 'Not Plantable')
                tree = 'Has Tree' if has else ('Can Plant' if plantable else 'Cannot Plant')
                
                popup = f"<b>Location (Refine Lvl {rl})</b><br><b>{status}</b><br><b>{tree}</b><br><b>Land Type:</b> {lt}<br><b>Pollution:</b> {poll:.1f} ug/m3<br><b>Temperature:</b> {temp:.1f}C<br><b>Score:</b> {score:.1f}"
                
                data.append({'lat': lat, 'lon': lon, 'color': color, 'radius': 6 + rl * 2, 'popup': popup})
        return data
    
    def run_selected_algorithm(self):
        if not self.city_graph or len(self.city_graph.nodes) == 0:
            self.log("No data. Draw a polygon first.", "WARNING")
            messagebox.showwarning("No Data", "Please draw a polygon on the map first.")
            return
        
        try:
            max_trees = int(self.max_trees.get()) if self.max_trees else 100
        except:
            max_trees = 100
        
        self.set_status(f"Finding optimal locations for {max_trees} trees...", show_progress=True)
        
        try:
            decisions = self.planner.run_optimization_auto(max_trees=max_trees, min_distance=10.0)
            if decisions:
                selected = [nid for nid, val in decisions.items() if val == 1]
                for nid in selected:
                    if nid in self.city_graph.nodes:
                        self.city_graph.nodes[nid].planted_trees = 1
                self.sync_current_points_from_graph()
                self._show_trees_from_selected(selected)
                messagebox.showinfo("Complete!", f"Successfully placed {len(selected)} trees!\n\nTrees are now displayed on the map.")
            else:
                messagebox.showwarning("No solution", "Could not find optimal locations.\nTry reducing the number of trees.")
        except Exception as e:
            self.log(f"Error: {e}", "ERROR")
            messagebox.showerror("Error", f"Error: {e}")
        finally:
            self.set_status("Ready", show_progress=False)
    
    def _show_trees_from_selected(self, node_ids):
        if not hasattr(self, 'map_view'):
            return
        trees = []
        for nid in node_ids:
            if nid in self.city_graph.nodes:
                loc = self.city_graph.nodes[nid]
                lat, lon = loc.get_location()
                trees.append({'lat': lat, 'lon': lon, 'color': '#2ecc71', 'radius': 12,
                             'icon': '🌳', 'popup': f"🌳 Planted Tree<br>Location: {nid}<br>Score: {loc.score:.1f}<br>Land Type: {loc.land_type}"})
        if trees:
            self.map_view.update_map_points(trees)
            self.log(f"Displayed {len(trees)} trees")
    
    def log(self, msg, level="INFO"):
        print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] [{level}] {msg}")
    
    def set_status(self, msg, show_progress=False):
        self.progress_label.config(text=msg)
        if show_progress:
            self.progress_bar.start()
        else:
            self.progress_bar.stop()
        self.root.update()
    
    def show_welcome_message(self):
        self.log("TERRA BRAIN - SMART TREE PLACEMENT SYSTEM\n" + "="*60)