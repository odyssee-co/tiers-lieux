import pandas as pd
import geopandas as gpd
from esda.adbscan import ADBSCAN

def top_50_muni(processed_path, exclude=[]):
    """
    Return the top 50 municipalities with the most inhabitants
    leaving every days to go to work in another communes.
    """
    persons_df = pd.read_feather(processed_path+"/persons.feather")
    persons_df = persons_df[persons_df["origin_id"]
                                    != persons_df["destination_id"]]
    #we exclude Toulouse from the list of candidates

    persons_df = persons_df[~persons_df.origin_id.isin(exclude)]
    top_50 = list(persons_df["origin_id"].value_counts()[0:50].index)
    return top_50


def top_50_clusters(processed_path, eps=5000, min_samples=100):
    """
    Return the top 50 adbscan cluster centroids with the most inhabitants
    leaving every days to go to work in another communes.
    """
    persons_df = pd.read_feather(processed_path+"/persons.feather")
    persons_df = persons_df[persons_df["origin_id"]
                                    != persons_df["destination_id"]]

    df = persons_df.groupby("origin_id").sum()
    municipalities = gpd.read_file(f"{processed_path}/communes.gpkg")
    pop_df = df.merge(municipalities, how="left", left_on="origin_id",
                      right_on="commune_id")[["commune_id", "weight", "x", "y"]]
    pop_df.rename(columns={"x":"X", "y":"Y"}, inplace=True)
    adbs = ADBSCAN(eps, min_samples, pct_exact=1, keep_solus=True)
    adbs.fit(pop_df, sample_weight=pop_df["weight"])
    #from IPython import embed; embed()
    print(adbs.votes[adbs.votes["lbls"].astype("int")>0])
    top_50 = list(persons_df["origin_id"].value_counts()[0:50].index)

    return top_50
