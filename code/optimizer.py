from itertools import combinations
from tqdm import tqdm
import numpy as np


def eval(selectedOffices_df):
    return selectedOffices_df.max(axis=1).sum()

def eval_idx(saved_df, selected_offices_idx):
    selectedOffices_df = saved_df.iloc[:, selected_offices_idx]
    return eval(selectedOffices_df)


def brute_force(saved_df, n):
    """
    Enumerate all the possible combinations of selecting n offices amongst the
    ones in saved_df (matrix of distance saved by each user if they go to work
    in each offices and return the best combination in term of overall saved
    distance.
    """
    nb_offices = saved_df.shape[1]
    possibleCombinations = combinations(range(nb_offices), n)
    best = (0, [])
    for selectedOffices in tqdm(possibleCombinations):
        total_saved_distance = eval_idx(saved_df, list(selectedOffices))
        if total_saved_distance > best[0]:
            best = (total_saved_distance, list(saved_df.columns[list(selectedOffices)]))
    print(best)
    return best


def n_best(saved_df, n):
    n_best = list(saved_df.sum().sort_values(ascending=False).iloc[0:n].index)
    selectedOffices_df = saved_df.loc[:, n_best]
    return (eval(selectedOffices_df), n_best)


def random(saved_df, n, nb_it):
    best = n_best(saved_df, n)
    i = 0
    while i < nb_it:
        i += 1
        sample = saved_df.sample(n, axis=1)
        res = eval(sample)
        if res > best[0]:
            i = 0
            best = (res, list(sample.columns))
            print(best)
    return best


def random_weighted(saved_df, n, nb_it):
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
            print(best)
    return best


def evolutionary(saved_df, n, ratio, nb_it):
    best = n_best(saved_df, n)
    i = 0
    sample = saved_df.sample(n, axis=1)
    while i < nb_it:
        i += 1
        res = eval(sample)
        if res > best[0]:
            i = 0
            best = (res, list(sample.columns))
            print(best)
        nb_to_keep = round(n * ratio)
        w = np.power(sample.idxmax(axis=1).value_counts(), 2)  #weight is how many times each office is the best choice for one employee with the current selection; pow to be conservative
        sample1 = sample.sample(nb_to_keep, axis=1, weights = w) #we keep a ratio of the pop with a higher prob for best performing
        sample2 = saved_df.drop(sample.columns, axis=1).sample(n-nb_to_keep, axis=1) #we complete with random in the remainings pop
        sample = sample1.join(sample2)
    return best
