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


def top_50_clusters(processed_path, eps=3000, min_samples=500):
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
                      right_on="commune_id")[["commune_id", "weight", "x", "y", "geometry"]]
    pop_df.rename(columns={"x":"X", "y":"Y"}, inplace=True)
    adbs = ADBSCAN(eps, min_samples, pct_exact=1, keep_solus=True)
    adbs.fit(pop_df, sample_weight=pop_df["weight"])
    print(f"nb_kernels: {adbs.votes.lbls.astype(int).max()}")
    #print(f"nb_classified{len(adbs.votes[adbs.votes["lbls"].astype("int")>0])}")
    print(f"nb_classified: {len(adbs.votes[adbs.votes['lbls'].astype('int')>0])}")

    df = pop_df.join(adbs.votes.lbls)
    df = df[df.lbls!="-1"]
    top_50_lbls = df.groupby("lbls").weight.sum().sort_values(ascending=False)[:50]

    top_50 = []
    for lbl in top_50_lbls.index:
        cluster = df[df.lbls == lbl]
        centroid = gpd.geodataframe.GeoDataFrame(cluster).dissolve().centroid
        from IPython import embed; embed()
        top_50.append(municipalities[municipalities.contains(centroid)][0]) #tofix
    #top_50 = list(persons_df["origin_id"].value_counts()[0:50].index)

    return top_50
