import tkinter as tk
from tkinter import ttk


class ControlPanel:
    
    def __init__(self, parent, main_window):
        self.parent = parent
        self.main = main_window
        self.setup_controls()
        
    def setup_controls(self):
        
        lf1 = ttk.LabelFrame(self.parent, text="Problem")
        lf1.pack(fill=tk.X, pady=5)
        ttk.Label(lf1, text="Goal:", font=('Arial', 10, 'bold')).pack(anchor=tk.W)
        ttk.Label(lf1, text="Reduce Pollution + Temperature", font=('Arial', 9)).pack(anchor=tk.W, padx=10)
        
        lf2 = ttk.LabelFrame(self.parent, text="Agent")
        lf2.pack(fill=tk.X, pady=5)
        ttk.Label(lf2, text="Type: Goal-Based Agent").pack(anchor=tk.W)
        
        lf3 = ttk.LabelFrame(self.parent, text="Optimization")
        lf3.pack(fill=tk.X, pady=5)
        ttk.Button(lf3, text="Hill Climbing", command=self.main.run_hill_climbing).pack(fill=tk.X, pady=2)
        ttk.Button(lf3, text="Genetic Algorithm", command=self.main.run_genetic).pack(fill=tk.X, pady=2)
        
        ttk.Label(lf3, text="GA Population:").pack(anchor=tk.W)
        self.ga_pop = ttk.Scale(lf3, from_=10, to=200, orient=tk.HORIZONTAL)
        self.ga_pop.set(50)
        self.ga_pop.pack(fill=tk.X)
        
        lf4 = ttk.LabelFrame(self.parent, text="CSP Settings")
        lf4.pack(fill=tk.X, pady=5)
        ttk.Label(lf4, text="Max Trees:").pack(anchor=tk.W)
        self.max_trees = ttk.Entry(lf4)
        self.max_trees.insert(0, "100")
        self.max_trees.pack(fill=tk.X)
        ttk.Label(lf4, text="Min Distance (m):").pack(anchor=tk.W)
        self.min_distance = ttk.Entry(lf4)
        self.min_distance.insert(0, "10")
        self.min_distance.pack(fill=tk.X)
        
        lf5 = ttk.LabelFrame(self.parent, text="Map Settings")
        lf5.pack(fill=tk.X, pady=5)
        ttk.Label(lf5, text="Grid Size (points):").pack(anchor=tk.W)
        self.grid_size_entry = ttk.Entry(lf5, width=10)
        self.grid_size_entry.insert(0, "4")
        self.grid_size_entry.pack(anchor=tk.W, padx=5, pady=2)
        ttk.Label(lf5, text="Step (degrees):").pack(anchor=tk.W)
        self.step_entry = ttk.Entry(lf5, width=10)
        self.step_entry.insert(0, "0.02")
        self.step_entry.pack(anchor=tk.W, padx=5, pady=2)
        
        lf6 = ttk.LabelFrame(self.parent, text="Polygon Drawing")
        lf6.pack(fill=tk.X, pady=5)
        ttk.Label(lf6, text="Spacing (meters):").pack(anchor=tk.W)
        self.polygon_spacing = ttk.Entry(lf6, width=10)
        self.polygon_spacing.insert(0, "500")
        self.polygon_spacing.pack(anchor=tk.W, padx=5, pady=2)
        ttk.Button(lf6, text="Enable Polygon Drawing", command=self.main.enable_polygon_drawing).pack(fill=tk.X, pady=5)
        
        lf7 = ttk.LabelFrame(self.parent, text="Refine")
        lf7.pack(fill=tk.X, pady=5)
        self.refine_button = ttk.Button(lf7, text="Refine Points (Add Midpoints)",
                                        command=self.main.refine_points, state='disabled')
        self.refine_button.pack(fill=tk.X, pady=2)
        self.main.refine_button = self.refine_button
        
        lf8 = ttk.LabelFrame(self.parent, text="Actions")
        lf8.pack(fill=tk.X, pady=5)
        ttk.Button(lf8, text="Show Map", command=self.main.show_map).pack(fill=tk.X, pady=2)
        ttk.Button(lf8, text="Clear Console", command=lambda: self.main.console.delete(1.0, tk.END)).pack(fill=tk.X, pady=2)
