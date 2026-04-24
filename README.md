# 🌳 Terra Brain

**Smart Urban Tree Placement System using AI & CSP**

---

## 📌 Overview

**Terra Brain** is an intelligent system designed to optimize urban green space planning by selecting the best tree planting locations using **Constraint Satisfaction Problem (CSP)** and optimization algorithms.

### 🎯 Project Goal

* 🌫️ Reduce air pollution
* 🌡️ Lower urban temperatures
* 🌳 Improve distribution of green spaces

---

## 🎯 Problem & Solution

| Problem                    | Solution                           |
| -------------------------- | ---------------------------------- |
| High pollution levels      | Target polluted areas for planting |
| Urban heat islands         | Cooling effect through trees       |
| Uneven green distribution  | Smart optimization algorithms      |
| Manual analysis complexity | Automated AI-based decision making |

---

## ✨ Features

* 🗺️ Interactive map with polygon drawing
* 🤖 Multiple AI algorithms (Greedy / Genetic / Backtracking / Hill Climbing)
* 📊 Environmental data analysis
* 🔥 Pollution heatmap visualization
* 🌳 Tree placement visualization
* 🔄 Adjustable sampling resolution

---

## 🏗️ Project Structure

```
Terra Brain/
├── main.py                 # Main entry point
├── csp/                    # Constraint satisfaction module
│   ├── checker.py
│   └── constraints.py
├── data/                   # Data fetching module
│   ├── data_loader.py
│   └── real_data_fetcher.py
├── models/                 # Data models
│   ├── city_graph.py
│   ├── grid_sampler.py
│   └── location.py
├── optimization/           # Optimization algorithms
│   └── solvers.py
├── problem/                # Problem formulation
│   ├── state.py
│   ├── objective.py
│   └── variables.py
└── ui/                     # User interface
    ├── main_window.py
    ├── map_view_qt.py
    ├── colors.py
    └── controls.py
```

---

## ⚙️ How It Works

```
1. Select a city
2. Draw target area (polygon)
3. Generate grid points
4. Fetch environmental data
5. Apply CSP constraints
6. Run optimization algorithm
7. Display optimal tree locations 🌳
```

---

## 🧠 CSP Constraints

* 🌱 Maximum number of trees (budget constraint)
* 📏 Minimum distance between trees
* 🌍 Valid land conditions
* 📍 Location suitability checks

---

## 🧮 Algorithms

| Algorithm         | Use Case                               |
| ----------------- | -------------------------------------- |
| Backtracking      | Small datasets (exact solution)        |
| Genetic Algorithm | Medium datasets (balanced performance) |
| Hill Climbing     | Large datasets (fast approximation)    |

---

## 📊 Objective Function

```
Score = 0.5 × Pollution + 0.3 × Land + 0.2 × Temperature
```

---

## 📦 Requirements

```
PyQt5
numpy
shapely
aiohttp
requests
folium
Pillow
```

---

## 🗺️ Data Sources

* Open-Meteo → Weather & pollution data
* OpenStreetMap (Nominatim) → Geocoding
* Folium → Interactive maps

---

قولّي 👍
