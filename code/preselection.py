import pandas as pd
import geopandas as gpd
from esda.adbscan import ADBSCAN

def get_top_50_municipalities(data_path, exclude=[]):
    """
    Return the top 50 municipalities with the most inhabitants
    leaving every days to go to work in another communes.
    """
    persons_df = pd.read_csv(data_path+"/processed/persons.csv", dtype=str)
    persons_df = persons_df[persons_df["origin_id"]
                                    != persons_df["destination_id"]]
    #we exclude Toulouse from the list of candidates

    persons_df = persons_df[~persons_df.origin_id.isin(exclude)]
    top_50 = list(persons_df["origin_id"].value_counts()[0:50].index)
    return top_50


def get_top_50_clusters(data_path, eps=5000, min_samples=100):
    """
    Return the top 50 adbscan cluster centroids with the most inhabitants
    leaving every days to go to work in another communes.
    """
    persons_df = pd.read_csv(data_path+"/processed/persons.csv", dtype=str)
    persons_df = persons_df[persons_df["origin_id"].astype(str)
                                    != persons_df["destination_id"].astype(str)]
    geometry=gpd.points_from_xy(persons_df.origin_x,
                                persons_df.origin_y,
                                crs="EPSG:2154")
    persons_df = gpd.GeoDataFrame(persons_df, geometry=geometry)
    pop = persons_df["origin_id"].value_counts()
    pop_df = pd.DataFrame({'origin_id':pop.index, 'population':pop.values})
    pop_df = pd.merge(pop_df, persons_df[["origin_id", "geometry"]],
                          on="origin_id", how="left")
    pop_df = pop_df[~pop_df.origin_id.duplicated()]
    pop_df = gpd.GeoDataFrame(pop_df)
    pop_df["X"] = pop_df.geometry.x
    pop_df["Y"] = pop_df.geometry.y
    pop_df = pop_df.dropna()
    adbs = ADBSCAN(eps, min_samples, pct_exact=1, keep_solus=True)
    #adbs.fit(pop_df)
    adbs.fit(pop_df, sample_weight=pop_df["population"])
    from IPython import embed; embed()
    #print(adbs.votes[adbs.votes["lbls"].astype("int")>0])
    top_50 = list(persons_df["origin_id"].value_counts()[0:50].index)

    return top_50
