import numpy as np
import pyomo.environ as pyo
from multiprocessing import Pool
from functools import partial
import time, math, os


def eval(saved_df):
    """
    Evaluate the total saved distance if each employee chose the closest office
    amongst the subset selectedOffices.

    Parameters:
    - saved_df (pd.DataFrame): DataFrame containing saved distances data.

    Returns:
    - total_saved_distance (float): Total saved distance when employees choose
                                   the closest office from the selected offices.
    """
    return saved_df.max(axis=1).sum()


def n_best(saved_df, n):
    """
    Return the n offices that would save the most travel time individually,
    useful to get a lower bound to the optimization problem.

    Parameters:
    - saved_df (pd.DataFrame): DataFrame containing saved distances data.
    - n (int): Number of offices to select.

    Returns:
    - total_saved_distance (float): Total saved distance when selecting n best offices.
    - selected_offices (list): List of n offices selected based on maximum saved distances.
    """
    n_best = list(saved_df.sum().sort_values(ascending=False).iloc[0:n].index)
    selectedOffices_df = saved_df.loc[:, n_best]
    return (eval(selectedOffices_df), n_best)


def random(saved_df, n, verbose=False, nb_it=3000):
    """
    Randomly select a subset of offices and return the best subset if nb_it iterations
    pass without improving the result.

    Parameters:
    - saved_df (pd.DataFrame): DataFrame containing saved distances data.
    - n (int): Number of offices to select.
    - verbose (bool, optional): Whether to print verbose output. Default is False.
    - nb_it (int, optional): Number of iterations without improvement to stop the search. Default is 3000.

    Returns:
    - best_subset (tuple): Tuple containing the total saved distance and the list of selected offices.
    """
    best = n_best(saved_df, n)
    i = 0
    while i < nb_it:
        i += 1
        sample = saved_df.sample(n, axis=1)
        res = eval(sample)
        if res > best[0]:
            i = 0
            best = (res, list(sample.columns))
            if verbose:
                print(best)
    return best


def random_weighted(saved_df, n, verbose=False, nb_it=3000):
    """
    Randomly select a subset of offices weighted by their individual performances,
    and return the best subset if nb_it iterations pass without improving the result.

    Parameters:
    - saved_df (pd.DataFrame): DataFrame containing saved distances data.
    - n (int): Number of offices to select.
    - verbose (bool, optional): Whether to print verbose output. Default is False.
    - nb_it (int, optional): Number of iterations without improvement to stop the search. Default is 3000.

    Returns:
    - best_subset (tuple): Tuple containing the total saved distance and the list of selected offices.
    """
    best = n_best(saved_df, n)
    i = 0
    w = np.sqrt(saved_df.sum()) #weight is the total distance a single office would saved; sqrt to favor novelties
    while i < nb_it:
        i += 1
        sample = saved_df.sample(n, axis=1, weights = w)
        res = eval(sample)
        if res > best[0]:
            i = 0
            best = (res, list(sample.columns))
            if verbose:
                print(best)
    return best

def random_weighted_worker(n, id):
    """
    Worker function for parallel random weighted selection algorithm.

    Parameters:
    - n (int): Number of offices to select.
    - id (int): Worker ID for identification.

    Returns:
    - result (tuple): Tuple containing the total saved distance and the list of selected offices.
    """
    np.random.seed((os.getpid() * int(time.time())) % 123456789)
    w = global_w
    saved_df = global_saved_df
    sample = saved_df.sample(n, axis=1, weights=w)
    res = eval(sample)
    return (res, list(sample.columns))

def p_random_weighted(saved_df, n, verbose=False, nb_it=3000, nb_threads=10):
    """
    Parallel implementation of the random_weighted algorithm.

    Parameters:
    - saved_df (pd.DataFrame): DataFrame containing saved distances data.
    - n (int): Number of offices to select.
    - verbose (bool, optional): Whether to print verbose output. Default is False.
    - nb_it (int, optional): Number of iterations without improvement to stop the search. Default is 3000.
    - nb_threads (int, optional): Number of parallel threads to use. Default is 10.

    Returns:
    - best_subset (tuple): Tuple containing the total saved distance and the list of selected offices.
    """
    global global_saved_df
    global global_w
    best = n_best(saved_df, n)
    global_w = np.sqrt(saved_df.sum()) #weight is the total distance a single office would saved; sqrt to favor novelties
    global_saved_df = saved_df
    with Pool(nb_threads) as p:
        i = 0
        while i < nb_it/nb_threads:
            res = p.map(partial(random_weighted_worker, n), range(nb_threads))
            gen_best = res[0]
            for r in res[1:nb_threads]:
                if r[0] > gen_best[0]:
                    gen_best = r
            if gen_best[0] > best[0]:
                best = gen_best
                i=0
                if verbose:
                    print(best)
            i += 1
    return best


def evolutionary(saved_df, n, verbose=False, ratio=0.5, nb_it=1000):
    """
    Evolutionary algorithm that keeps a ratio of the population weighted by their
    performance in the current subset and returns the best subset if nb_it iterations
    pass without improving the result.

    Parameters:
    - saved_df (pd.DataFrame): DataFrame containing saved distances data.
    - n (int): Number of offices to select.
    - verbose (bool, optional): Whether to print verbose output. Default is False.
    - ratio (float, optional): Ratio of the population to keep in each iteration. Default is 0.5.
    - nb_it (int, optional): Number of iterations without improvement to stop the search. Default is 1000.

    Returns:
    - best_subset (tuple): Tuple containing the total saved distance and the list of selected offices.
    """
    best = n_best(saved_df, n)
    #sample = saved_df[best[1]]
    i = 0
    sample = saved_df.sample(n, axis=1)
    w_single = np.power(saved_df.sum(),2)
    #w_single = saved_df.sum()
    while i < nb_it:
        i += 1
        res = eval(sample)
        if res > best[0]:
            i = 0
            best = (res, list(sample.columns))
            if verbose:
                print(best)
        nb_to_keep = round(n * ratio)

        #calculate weight
        s = sample[sample.sum(axis=1)>0]
        s_max = np.power(s.idxmax(axis=1).value_counts(), 2)  #weight is how many times each office is the best choice for one employee with the current selection; pow to be conservative
        #s_max = s.idxmax(axis=1).value_counts()  #weight is how many times each office is the best choice for one employee with the current selection; pow to be conservative
        #s_max = np.sqrt(s.idxmax(axis=1).value_counts())  #weight is how many times each office is the best choice for one employee with the current selection; pow to be conservative
        w = []
        for m in sample.columns:
            if m in s_max.index:
                w.append(s_max[m])
            else:
                w.append(0.1)

        sample1 = sample.sample(nb_to_keep, axis=1, weights = w) #we keep a ratio of the pop with a higher prob for best performing

        sample2 = saved_df.drop(sample.columns, axis=1).sample(n-nb_to_keep, axis=1, weights=w_single.drop(sample.columns)) #we complete with random in the remainings pop
        sample = sample1.join(sample2)
    return best

def evolutionary_worker(n, ratio, prev_best, id):
    """
    Worker function for parallel evolutionary algorithm.

    Parameters:
    - n (int): Number of offices to select.
    - ratio (float): Ratio of the population to keep in each iteration.
    - prev_best (tuple): Previous best subset containing total saved distance and selected offices.
    - id (int): Worker ID for identification.

    Returns:
    - result (tuple): Tuple containing the total saved distance and the list of selected offices.
    """
    saved_df = global_saved_df
    np.random.seed((os.getpid() * int(time.time())) % 123456789)
    sample = saved_df[prev_best[1]]
    nb_to_keep = round(n * ratio)
    s = sample[sample.sum(axis=1)>0]
    s_max = np.power(s.idxmax(axis=1).value_counts(), 2)  #weight is how many times each office is the best choice for one employee with the current selection; pow to be conservative
    w = []
    for m in sample.columns:
        if m in s_max.index:
            w.append(s_max[m])
        else:
            w.append(0.1)
    sample1 = sample.sample(nb_to_keep, axis=1, weights = w) #we keep a ratio of the pop with a higher prob for best performing
    sample2 = saved_df.drop(sample.columns, axis=1).sample(n-nb_to_keep, axis=1, weights=global_w_single.drop(sample.columns)) #we complete with random in the remainings pop
    sample = sample1.join(sample2)
    res = eval(sample)
    return (res, list(sample.columns))

def p_evolutionary(saved_df, n, verbose=False, ratio=0.5, nb_it=1000, nb_threads=10):
    """
    Parallel implementation of the Evolutionary algorithm.

    Parameters:
    - saved_df (pd.DataFrame): DataFrame containing saved distances data.
    - n (int): Number of offices to select.
    - verbose (bool, optional): Whether to print verbose output. Default is False.
    - ratio (float, optional): Ratio of the population to keep in each iteration. Default is 0.5.
    - nb_it (int, optional): Number of iterations without improvement to stop the search. Default is 1000.
    - nb_threads (int, optional): Number of parallel threads to use. Default is 10.

    Returns:
    - best_subset (tuple): Tuple containing the total saved distance and the list of selected offices.
    """
    global global_saved_df
    global global_w_single
    best = n_best(saved_df, n)
    prev_best = best
    global_saved_df = saved_df
    global_w_single = np.power(saved_df.sum(),2)
    with Pool(nb_threads) as p:
        i = 0
        while i < nb_it/nb_threads:
            res = p.map(partial(evolutionary_worker, n, ratio, prev_best), np.arange(1, nb_threads+1))
            gen_best = res[0]
            for r in res[1:nb_threads]:
                if r[0] > gen_best[0]:
                    gen_best = r
            if gen_best[0] > best[0]:
                best = gen_best
                i=0
                if verbose:
                    print(best)
            prev_best = gen_best
            i += 1
    return best


def mip(saved_df, nb_offices, solver="cbc", verbose=False):
    """
    Mixed Integer Programming model for office location optimization using Pyomo.

    Parameters:
    - saved_df (pd.DataFrame): DataFrame containing saved distances data.
    - nb_offices (int): Number of offices to select.
    - solver (str, optional): Solver to use for optimization. Default is "cbc".
    - verbose (bool, optional): Whether to print verbose output. Default is False.

    Returns:
    - result (tuple): Tuple containing the total saved distance and the list of selected offices.
    """
    model = pyo.ConcreteModel()
    model.offices = range(saved_df.shape[1])
    model.employees = range(saved_df.shape[0])
    model.x = pyo.Var(model.employees, model.offices, within=pyo.Binary)
    model.y = pyo.Var(model.offices, within=pyo.Binary)

    model.obj = pyo.Objective(expr=sum(saved_df.iloc[e,o]*model.x[e,o]
        for o in model.offices for e in model.employees), sense=pyo.maximize)

    #employees can not choose more than one office
    model.single_x = pyo.ConstraintList()
    for e in model.employees:
        model.single_x.add(sum(model.x[e,o] for o in model.offices) <= 1)

    #an employee can only work to an office if it is selected
    model.bound_y = pyo.ConstraintList()
    for o in model.offices:
        for e in model.employees:
            model.bound_y.add(model.x[e,o] <= model.y[o])

    #nb_offices offices are selected
    model.num_facilities = pyo.Constraint(expr=sum(model.y[o] for o in model.offices)==nb_offices)

    if solver == "cbc":
        instance = pyo.SolverFactory(solver, options={"threads": 10})
    else:
        instance = pyo.SolverFactory(solver)
    #instance = SolverFactory("cbc", options={"threads": 4}) # cbc needs to be compiled multi-threaded
    instance.solve(model)

    selected_communes = np.array([pyo.value(v)==1 for v in model.y.values()])
    res = (pyo.value(model.obj), list(saved_df.columns[selected_communes]))
    if verbose:
        print(res)
    return res
