from itertools import combinations
from tqdm import tqdm

def brute_force(saved_df, n):
    """
    Enumerate all the possible combinations of selecting n offices amongst the
    one in saved_df and return the best combination in term of overall saved
    distance.
    """
    nb_offices = saved_df.shape[1]
    possibleCombinations = combinations(range(nb_offices), n)
    best = (0, [])
    for selectedOffices in tqdm(possibleCombinations):
        selectedOffices_df = saved_df.iloc[:, list(selectedOffices)]
        selectedOffices_df["max"] = selectedOffices_df.max(axis=1)
        total_saved_distance = selectedOffices_df["max"].sum()
        if total_saved_distance > best[0]:
            best = (total_saved_distance, selectedOffices)
    return best
