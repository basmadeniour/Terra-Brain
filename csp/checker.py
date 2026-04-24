from csp.constraints import composite_constraint


def check_constraints(state, decisions, max_trees=100, min_distance=10):
    return composite_constraint(state, decisions, max_trees, min_distance)


def is_consistent(state, decisions, var, value, max_trees=100, min_distance=10):
    temp = decisions.copy()
    temp[var] = value
    return composite_constraint(state, temp, max_trees, min_distance)