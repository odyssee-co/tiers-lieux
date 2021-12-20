from itertools import combinations
from tqdm import tqdm


def eval(selectedOffices_df):
    return selectedOffices_df.max(axis=1).sum()


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
        selectedOffices_df = saved_df.iloc[:, list(selectedOffices)]
        total_saved_distance = eval(selectedOffices_df)
        if total_saved_distance > best[0]:
            best = (total_saved_distance, selectedOffices)
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
        sample = saved_df.sample(10, axis=1)
        res = eval(sample)
        if res > best[0]:
            i = 0
            best = (res, list(sample.columns))
            print(best)
    return best


def random_weighted(saved_df, n, nb_it):
    best = n_best(saved_df, n)
    i = 0
    w = saved_df.sum()
    while i < nb_it:
        i += 1
        sample = saved_df.sample(10, axis=1, weights = w)
        res = eval(sample)
        if res > best[0]:
            i = 0
            best = (res, list(sample.columns))
            print(best)
    return best
