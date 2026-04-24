"""
Optimization Solvers Module for Urban Green AI

This module contains all optimization algorithms used in the system:
- Greedy Search: Fast heuristic for large problems
- Backtracking CSP: Exact solver with MRV heuristic for small problems
- Hill Climbing: Local search refinement
- Genetic Algorithm: Evolutionary optimization for medium problems
- Hybrid Solver: Auto-selects best strategy based on problem size
"""

from .solvers import (
    GreedySolver,
    BacktrackingSolver,
    HillClimbingSolver,
    GeneticSolver,
    HybridSolver,
    CSPOptimizer
)

__all__ = [
    'GreedySolver',
    'BacktrackingSolver',
    'HillClimbingSolver',
    'GeneticSolver',
    'HybridSolver',
    'CSPOptimizer'
]