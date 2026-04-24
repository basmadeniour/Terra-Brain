# Terra Brain

**AI-Powered Urban Tree Optimization System using CSP**

---

## Overview

Terra Brain is an intelligent geospatial decision-support system designed to optimize urban green space planning.
It selects optimal tree planting locations using Constraint Satisfaction Problem (CSP) techniques and optimization algorithms.

---

## Project Objective

This system aims to:

* Reduce urban air pollution
* Mitigate urban heat island effects
* Improve spatial distribution of green infrastructure

---

## Problem Statement & Approach

| Challenge                     | Proposed Solution                                  |
| ----------------------------- | -------------------------------------------------- |
| High pollution concentration  | Prioritize polluted zones for planting             |
| Urban heat accumulation       | Apply cooling effects via vegetation modeling      |
| Uneven green coverage         | Optimize spatial distribution using AI             |
| Manual environmental analysis | Automate decision-making with computational models |

---

## Key Features

* Interactive GIS-style map interface
* Polygon-based region selection
* Multi-algorithm optimization engine (Greedy / Genetic / Backtracking / Hill Climbing)
* Environmental data integration and analysis
* Pollution heatmap visualization
* Tree placement simulation layer
* Adjustable spatial resolution

---

## System Architecture

```
Terra Brain/
├── main.py                 → Application entry point
├── csp/                    → Constraint Satisfaction layer
│   ├── checker.py
│   └── constraints.py
├── data/                   → Data acquisition layer
│   ├── data_loader.py
│   └── real_data_fetcher.py
├── models/                 → Core data structures
│   ├── city_graph.py
│   ├── grid_sampler.py
│   └── location.py
├── optimization/           → Optimization algorithms
│   └── solvers.py
├── problem/                → Problem formulation layer
│   ├── state.py
│   ├── objective.py
│   └── variables.py
└── ui/                     → User interface layer
    ├── main_window.py
    ├── map_view_qt.py
    ├── colors.py
    └── controls.py
```

---

## System Workflow

```
1. City selection
2. Region definition (polygon drawing)
3. Grid generation
4. Environmental data retrieval
5. CSP constraint evaluation
6. Optimization execution
7. Visualization of results
```

---

## Constraint Model (CSP)

* Maximum tree capacity (budget constraint)
* Minimum distance between trees
* Land suitability validation
* Spatial feasibility checks

---

## Optimization Algorithms

| Algorithm         | Description               | Use Case        |
| ----------------- | ------------------------- | --------------- |
| Backtracking      | Exhaustive search         | Small datasets  |
| Genetic Algorithm | Evolutionary optimization | Medium datasets |
| Hill Climbing     | Local search              | Large datasets  |

---

## Objective Function

```
Score = 0.5 × Pollution + 0.3 × Land + 0.2 × Temperature
```

---

## Dependencies

* PyQt5
* NumPy
* Shapely
* Aiohttp
* Requests
* Folium
* Pillow

---

## Data Sources

* Open-Meteo (weather & air quality)
* OpenStreetMap Nominatim (geocoding)
* Folium (map visualization)

---

## Vision

Terra Brain aims to support smarter urban planning through data-driven environmental optimization and sustainable green space design.
