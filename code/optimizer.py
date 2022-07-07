import numpy as np
import pyomo.environ as pyo


def eval(saved_df):
    """
    Return the total saved distance if each employee chose the closest office
    amongst the subset selectedOffices.
    """
    return saved_df.max(axis=1).sum()


def n_best(saved_df, n):
    """
    Return the n offices which would save the most travel time individualy
    (useful to get a lower bound to the optimization problem).
    """
    n_best = list(saved_df.sum().sort_values(ascending=False).iloc[0:n].index)
    selectedOffices_df = saved_df.loc[:, n_best]
    return (eval(selectedOffices_df), n_best)


def random(saved_df, n, verbose=False, nb_it=3000):
    """
    Randomly select a subset of offices, and return the best if nb_it iterations
    passed without improving the result.
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
    and return the best if nb_it iterations passed without improving the result.
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


def evolutionary(saved_df, n, verbose=False, ratio=0.8, nb_it=1000):
    """
    Evolutionary algorithm that keep a ratio of the population weighted by their
    performance in the current subset, and return the best if nb_it iterations
    passed without improving the result.
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


def mip(saved_df, nb_offices, solver="cbc", verbose=False):
    """
    MIP modelization in pyomo
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
        instance = pyo.SolverFactory(solver, options={"threads": 4})
    else:
        instance = pyo.SolverFactory(solver)
    #instance = SolverFactory("cbc", options={"threads": 4}) # cbc needs to be compiled multi-threaded
    instance.solve(model)

    selected_communes = np.array([pyo.value(v)==1 for v in model.y.values()])
    res = (pyo.value(model.obj), list(saved_df.columns[selected_communes]))
    if verbose:
        print(res)
    return res
