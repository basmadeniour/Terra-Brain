import random
import time
from csp.checker import check_constraints


class GreedySolver:
    
    def __init__(self, max_trees=100, min_distance=10):
        self.max_trees = max_trees
        self.min_distance = min_distance
        self.name = "Greedy Search"
        self.nodes_explored = 0
        self.pruned = 0
    
    def solve(self, state):
        decisions = {loc.node_id: 0 for loc in state.locations}
        
        locations_with_gain = []
        for loc in state.get_plantable_locations():
            gain = self._calculate_gain(loc)
            locations_with_gain.append((loc, gain))
        
        locations_with_gain.sort(key=lambda x: x[1], reverse=True)
        
        trees_planted = 0
        for loc, _ in locations_with_gain:
            self.nodes_explored += 1
            if trees_planted >= self.max_trees:
                break
            
            test = decisions.copy()
            test[loc.node_id] = 1
            
            if check_constraints(state, test, self.max_trees, self.min_distance):
                decisions[loc.node_id] = 1
                trees_planted += 1
            else:
                self.pruned += 1
        
        return decisions
    
    def _calculate_gain(self, loc):
        old_score = self._calc_score(loc.pollution, loc.temperature, loc.land_type)
        new_pollution = max(0, loc.pollution * 0.85)
        new_temp = max(0, loc.temperature - 2)
        new_score = self._calc_score(new_pollution, new_temp, loc.land_type)
        return new_score - old_score
    
    def _calc_score(self, pollution, temperature, land_type):
        p_norm = min(1.0, pollution / 200.0)
        t_norm = min(1.0, abs(temperature - 22.0) / 20.0)
        env = 100 * (1 - (0.6 * p_norm + 0.4 * t_norm))
        bonus = {'park': 10, 'forest': 15, 'agricultural': 10,
                 'grass': 5, 'empty': 0, 'residential': -5,
                 'industrial': -20, 'building': -30, 'road': -30}.get(land_type, 0)
        return max(0, min(100, env + bonus))
    
    def get_statistics(self):
        return {'nodes_explored': self.nodes_explored, 'pruned': self.pruned}


class BacktrackingSolver:
    
    def __init__(self, max_trees=100, min_distance=10):
        self.max_trees = max_trees
        self.min_distance = min_distance
        self.name = "Backtracking CSP"
        self.nodes_explored = 0
        self.pruned = 0
        self.best_solution = None
        self.best_score = -1
    
    def solve(self, state):
        self.nodes_explored = 0
        self.pruned = 0
        self.best_solution = None
        self.best_score = -1
        
        plantable = state.get_plantable_locations()
        if len(plantable) > 30:
            plantable.sort(key=lambda loc: loc.pollution, reverse=True)
            plantable = plantable[:30]
        
        variables = [loc.node_id for loc in plantable]
        self._backtrack(state, variables, {}, 0)
        
        decisions = {loc.node_id: 0 for loc in state.locations}
        if self.best_solution:
            decisions.update(self.best_solution)
        
        return decisions
    
    def _backtrack(self, state, variables, decisions, idx):
        self.nodes_explored += 1
        
        if not check_constraints(state, decisions, self.max_trees, self.min_distance):
            self.pruned += 1
            return False
        
        if idx >= len(variables):
            score = self._evaluate(state, decisions)
            if score > self.best_score:
                self.best_score = score
                self.best_solution = decisions.copy()
            return True
        
        var = variables[idx]
        loc = state.get_location_by_id(var)
        values = [1, 0] if loc.pollution > 50 else [0, 1]
        
        for val in values:
            temp = decisions.copy()
            temp[var] = val
            if check_constraints(state, temp, self.max_trees, self.min_distance):
                decisions[var] = val
                self._backtrack(state, variables, decisions, idx + 1)
                del decisions[var]
        
        return True
    
    def _evaluate(self, state, decisions):
        total = 0.0
        for loc in state.locations:
            if decisions.get(loc.node_id, 0) == 1:
                p = max(0, loc.pollution * 0.85)
                t = max(0, loc.temperature - 2)
                p_norm = min(1.0, p / 200.0)
                t_norm = min(1.0, abs(t - 22.0) / 20.0)
            else:
                p_norm = min(1.0, loc.pollution / 200.0)
                t_norm = min(1.0, abs(loc.temperature - 22.0) / 20.0)
            
            env = 100 * (1 - (0.6 * p_norm + 0.4 * t_norm))
            bonus = {'park': 10, 'forest': 15, 'agricultural': 10,
                     'grass': 5, 'empty': 0, 'residential': -5,
                     'industrial': -20, 'building': -30, 'road': -30}.get(loc.land_type, 0)
            total += max(0, min(100, env + bonus))
        return total
    
    def get_statistics(self):
        return {'nodes_explored': self.nodes_explored, 'pruned': self.pruned, 'best_score': self.best_score}


class HillClimbingSolver:
    
    def __init__(self, max_trees=100, min_distance=10):
        self.max_trees = max_trees
        self.min_distance = min_distance
        self.name = "Hill Climbing"
        self.iterations = 0
        self.improvements = 0
    
    def solve(self, state, initial_decisions=None):
        if initial_decisions is None:
            greedy = GreedySolver(self.max_trees, self.min_distance)
            decisions = greedy.solve(state)
        else:
            decisions = initial_decisions.copy()
        
        current_score = self._evaluate(state, decisions)
        self.iterations = 0
        self.improvements = 0
        improved = True
        
        while improved and self.iterations < 100:
            improved = False
            self.iterations += 1
            
            for loc in state.get_plantable_locations():
                if decisions.get(loc.node_id, 0) == 0:
                    test = decisions.copy()
                    test[loc.node_id] = 1
                    if check_constraints(state, test, self.max_trees, self.min_distance):
                        new_score = self._evaluate(state, test)
                        if new_score > current_score:
                            decisions = test
                            current_score = new_score
                            improved = True
                            self.improvements += 1
                            break
            
            if not improved:
                for loc in state.get_plantable_locations():
                    if decisions.get(loc.node_id, 0) == 1:
                        test = decisions.copy()
                        test[loc.node_id] = 0
                        new_score = self._evaluate(state, test)
                        if new_score > current_score:
                            decisions = test
                            current_score = new_score
                            improved = True
                            self.improvements += 1
                            break
            
            if not improved:
                for loc1 in state.get_plantable_locations():
                    if decisions.get(loc1.node_id, 0) == 1:
                        for loc2 in state.get_plantable_locations():
                            if decisions.get(loc2.node_id, 0) == 0 and loc1 != loc2:
                                test = decisions.copy()
                                test[loc1.node_id] = 0
                                test[loc2.node_id] = 1
                                if check_constraints(state, test, self.max_trees, self.min_distance):
                                    new_score = self._evaluate(state, test)
                                    if new_score > current_score:
                                        decisions = test
                                        current_score = new_score
                                        improved = True
                                        self.improvements += 1
                                        break
                        if improved:
                            break
        
        return decisions
    
    def _evaluate(self, state, decisions):
        total = 0.0
        for loc in state.locations:
            if decisions.get(loc.node_id, 0) == 1:
                p = max(0, loc.pollution * 0.85)
                t = max(0, loc.temperature - 2)
                p_norm = min(1.0, p / 200.0)
                t_norm = min(1.0, abs(t - 22.0) / 20.0)
            else:
                p_norm = min(1.0, loc.pollution / 200.0)
                t_norm = min(1.0, abs(loc.temperature - 22.0) / 20.0)
            
            env = 100 * (1 - (0.6 * p_norm + 0.4 * t_norm))
            bonus = {'park': 10, 'forest': 15, 'agricultural': 10,
                     'grass': 5, 'empty': 0, 'residential': -5,
                     'industrial': -20, 'building': -30, 'road': -30}.get(loc.land_type, 0)
            total += max(0, min(100, env + bonus))
        return total
    
    def get_statistics(self):
        return {'iterations': self.iterations, 'improvements': self.improvements}


class GeneticSolver:
    
    def __init__(self, max_trees=100, min_distance=10,
                 population_size=50, generations=50, mutation_rate=0.1):
        self.max_trees = max_trees
        self.min_distance = min_distance
        self.population_size = population_size
        self.generations = generations
        self.mutation_rate = mutation_rate
        self.name = "Genetic Algorithm"
        self.best_fitness = -1
        self.generations_run = 0
    
    def solve(self, state):
        plantable = state.get_plantable_locations()
        if not plantable:
            return {loc.node_id: 0 for loc in state.locations}
        
        pop = [self._random_individual(plantable) for _ in range(self.population_size)]
        best_individual = None
        self.best_fitness = -1
        self.generations_run = 0
        
        for gen in range(self.generations):
            self.generations_run = gen + 1
            fitness = []
            for ind in pop:
                f = self._fitness(state, ind, plantable)
                fitness.append(f)
                if f > self.best_fitness:
                    self.best_fitness = f
                    best_individual = ind.copy()
            
            new_pop = []
            for _ in range(self.population_size):
                p1 = self._tournament(pop, fitness)
                p2 = self._tournament(pop, fitness)
                child = self._crossover(p1, p2)
                if random.random() < self.mutation_rate:
                    child = self._mutate(child, plantable)
                new_pop.append(child)
            pop = new_pop
        
        decisions = {loc.node_id: 0 for loc in state.locations}
        for i, loc in enumerate(plantable):
            if best_individual[i] == 1:
                decisions[loc.node_id] = 1
        return decisions
    
    def _random_individual(self, plantable):
        ind = [0] * len(plantable)
        n = random.randint(1, min(self.max_trees, len(plantable)))
        for idx in random.sample(range(len(plantable)), n):
            ind[idx] = 1
        return ind
    
    def _fitness(self, state, individual, plantable):
        decisions = {loc.node_id: 0 for loc in state.locations}
        for i, loc in enumerate(plantable):
            if individual[i] == 1:
                decisions[loc.node_id] = 1
        if not check_constraints(state, decisions, self.max_trees, self.min_distance):
            return 0
        return self._evaluate(state, decisions)
    
    def _tournament(self, population, fitness, k=3):
        idx = random.sample(range(len(population)), k)
        best = max(idx, key=lambda i: fitness[i])
        return population[best].copy()
    
    def _crossover(self, p1, p2):
        point = random.randint(1, len(p1) - 1)
        child = p1[:point] + p2[point:]
        excess = sum(child) - self.max_trees
        if excess > 0:
            ones = [i for i, v in enumerate(child) if v == 1]
            random.shuffle(ones)
            for i in ones[:excess]:
                child[i] = 0
        return child
    
    def _mutate(self, individual, plantable):
        idx = random.randint(0, len(individual) - 1)
        individual[idx] = 1 - individual[idx]
        if sum(individual) > self.max_trees:
            individual[idx] = 0
        return individual
    
    def _evaluate(self, state, decisions):
        total = 0.0
        for loc in state.locations:
            if decisions.get(loc.node_id, 0) == 1:
                p = max(0, loc.pollution * 0.85)
                t = max(0, loc.temperature - 2)
                p_norm = min(1.0, p / 200.0)
                t_norm = min(1.0, abs(t - 22.0) / 20.0)
            else:
                p_norm = min(1.0, loc.pollution / 200.0)
                t_norm = min(1.0, abs(loc.temperature - 22.0) / 20.0)
            
            env = 100 * (1 - (0.6 * p_norm + 0.4 * t_norm))
            bonus = {'park': 10, 'forest': 15, 'agricultural': 10,
                     'grass': 5, 'empty': 0, 'residential': -5,
                     'industrial': -20, 'building': -30, 'road': -30}.get(loc.land_type, 0)
            total += max(0, min(100, env + bonus))
        return total
    
    def get_statistics(self):
        return {
            'population_size': self.population_size,
            'generations': self.generations_run,
            'best_fitness': self.best_fitness,
            'mutation_rate': self.mutation_rate
        }


class HybridSolver:
    
    def __init__(self, max_trees=100, min_distance=10, strategy='auto'):
        self.max_trees = max_trees
        self.min_distance = min_distance
        self.strategy = strategy
        self.name = "Hybrid Solver"
        self.stats = {}
        self.solver = None
    
    def solve(self, state):
        n_vars = len(state.get_plantable_locations())
        
        if self.strategy == 'auto':
            if n_vars <= 30:
                self.solver = BacktrackingSolver(self.max_trees, self.min_distance)
            elif n_vars <= 200:
                self.solver = GeneticSolver(self.max_trees, self.min_distance)
            else:
                self.solver = HillClimbingSolver(self.max_trees, self.min_distance)
        else:
            solvers = {
                'greedy': GreedySolver,
                'backtracking': BacktrackingSolver,
                'hill_climbing': HillClimbingSolver,
                'genetic': GeneticSolver
            }
            self.solver = solvers.get(self.strategy, GreedySolver)(self.max_trees, self.min_distance)
        
        start = time.time()
        decisions = self.solver.solve(state)
        elapsed = time.time() - start
        
        self.stats = {
            'strategy': self.solver.name,
            'time': elapsed,
            'trees': sum(1 for v in decisions.values() if v == 1),
            'variables': n_vars
        }
        
        return decisions
    
    def get_stats(self):
        return self.stats
    
    def get_statistics(self):
        if self.solver and hasattr(self.solver, 'get_statistics'):
            return self.solver.get_statistics()
        return self.stats


class CSPOptimizer:
    
    def __init__(self, method='greedy', max_trees=100, min_distance=10):
        self.method = method
        self.max_trees = max_trees
        self.min_distance = min_distance
        self.solver = None
        
        solvers = {
            'greedy': GreedySolver,
            'backtracking': BacktrackingSolver,
            'hill_climbing': HillClimbingSolver,
            'genetic': GeneticSolver,
            'hybrid': HybridSolver
        }
        solver_class = solvers.get(method, GreedySolver)
        self.solver = solver_class(max_trees, min_distance)
    
    def solve(self, state):
        return self.solver.solve(state)
    
    def get_statistics(self):
        if hasattr(self.solver, 'get_statistics'):
            return self.solver.get_statistics()
        return {}