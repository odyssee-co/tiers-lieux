import pandas as pd
import geopandas as gpd
from esda.adbscan import ADBSCAN
from sklearn.cluster import DBSCAN, KMeans
from sklearn.neighbors import KernelDensity
import numpy as np
import math

def all(processed_path, office_dep=None, office_muni=None, exclude=[]):
    """
    Return all municipalities minus the one in exclude.
    """
    municipalities = gpd.read_file(f"{processed_path}/communes.gpkg")
    if office_dep:
        municipalities = municipalities[municipalities.commune_id.str[:2].isin(office_dep)]
    if office_muni:
        municipalities = municipalities[municipalities.commune_id.isin(office_muni)]
    return list(set(municipalities.commune_id) - set(exclude))

def top_50(processed_path, office_dep=None, office_muni=None, exclude=[]):
    """
    Return the top 50 municipalities with the most inhabitants
    leaving every days to go to work in another communes.
    """
    persons_df = pd.read_feather(processed_path+"/persons.feather")
    persons_df = persons_df[persons_df["origin_id"]
                                    != persons_df["destination_id"]]
    persons_df = persons_df[~persons_df.origin_id.isin(exclude)]
    if office_dep:
        persons_df = persons_df[persons_df.origin_id.str[:2].isin(office_dep)]
    if office_muni:
        persons_df = persons_df[persons_df.origin_id.isin(office_muni)]
    return list(persons_df.groupby("origin_id").sum().sort_values(
                                          "weight", ascending=False)[:50].index)


def adbscan(processed_path, office_dep=None, office_muni=None, exclude=[], eps=4000, min_samples=500,
                    verbose=True):
    """
    Return the top adbscan cluster centres with the most inhabitants
    leaving every days to go to work in another communes.
    eps: maximum distance between two samples for them to be considered as in the same neighborhood.
    min_samples: number of samples (or total weight) in a neighborhood for a point to be considered as a core point. This includes the point itself.
    """
    persons_df = pd.read_feather(processed_path+"/persons.feather")
    persons_df = persons_df[persons_df["origin_id"]
                                    != persons_df["destination_id"]]
    persons_df = persons_df[~persons_df.origin_id.isin(exclude)]
    if office_dep:
        persons_df = persons_df[persons_df.origin_id.str[:2].isin(office_dep)]
    if office_muni:
        persons_df = persons_df[persons_df.origin_id.isin(office_muni)]
    df = persons_df.groupby("origin_id").sum()
    municipalities = gpd.read_file(f"{processed_path}/communes.gpkg")
    pop_df = df.merge(municipalities, how="left", left_on="origin_id",
                      right_on="commune_id")[["commune_id", "weight", "x", "y", "geometry"]]
    pop_df.rename(columns={"x":"X", "y":"Y"}, inplace=True)
    adbs = ADBSCAN(eps, min_samples, pct_exact=1, keep_solus=True)
    adbs.fit(pop_df, sample_weight=pop_df["weight"])
    if verbose:
        print("top_50_adbs:")
        print(f"  nb_muni: {len(municipalities)}")
        print(f"  nb_kernels: {len(set(adbs.votes.lbls))-1}")
        print(f"  nb_classified: {len(adbs.votes[adbs.votes['lbls'].astype('int')>0])}")
    df = pop_df[["weight", "geometry"]].join(adbs.votes.lbls)
    df = df[df.lbls!="-1"]
    df = gpd.geodataframe.GeoDataFrame(df).dissolve(by="lbls", aggfunc="sum")
    df = df.sort_values("weight", ascending=False)
    """
    ax = municipalities.plot()
    df.plot(ax=ax, facecolor='none', edgecolor='black', linewidth=3)
    plt.show()
    """

    best = []
    for k, v in df.iterrows():
        #use representative point instead of centroid in case of non convex shape
        rp = v.geometry.representative_point()
        id = municipalities[municipalities.contains(rp)].iloc[0].commune_id
        if id not in best:
            best.append(id)
        if len(best) == 50:
            break
    return best

def dbscan(processed_path, office_dep=None, office_muni=None, exclude=[], eps=4000, min_samples=500,
                    verbose=True):
    """
    Return the top dbscan cluster centres with the most inhabitants
    leaving every days to go to work in another communes.
    eps: maximum distance between two samples for them to be considered as in the same neighborhood.
    min_samples: number of samples (or total weight) in a neighborhood for a point to be considered as a core point. This includes the point itself.
    """
    eps=int(eps)
    persons_df = pd.read_feather(processed_path+"/persons.feather")
    persons_df = persons_df[persons_df["origin_id"]
                                    != persons_df["destination_id"]]
    persons_df = persons_df[~persons_df.origin_id.isin(exclude)]
    if office_dep:
        persons_df = persons_df[persons_df.origin_id.str[:2].isin(office_dep)]
    if office_muni:
        persons_df = persons_df[persons_df.origin_id.isin(office_muni)]
    df = persons_df.groupby("origin_id").sum()
    municipalities = gpd.read_file(f"{processed_path}/communes.gpkg")
    pop_df = df.merge(municipalities, how="left", left_on="origin_id",
                      right_on="commune_id")[["commune_id", "weight", "x", "y", "geometry"]]
    db = DBSCAN(eps=eps, min_samples=min_samples)
    coord = pop_df[["x", "y"]].values
    lbls = pd.Series(db.fit_predict(coord, sample_weight=pop_df["weight"]), name="lbls")

    if verbose:
        print("top_50_dbscan:")
        print(f"  nb_muni: {len(municipalities)}")
        print(f"  nb_kernels: {len(set(lbls))-1}")
        print(f"  nb_classified: {len(lbls[lbls>-1])}")

    df = pop_df[["weight", "geometry"]].join(lbls)
    df = df[df.lbls>-1]
    df = gpd.geodataframe.GeoDataFrame(df).dissolve(by="lbls", aggfunc="sum")
    df = df.sort_values("weight", ascending=False)

    best = []
    for k, v in df.iterrows():
        #use representative point instead of centroid in case of non convex shape
        rp = v.geometry.representative_point()
        id = municipalities[municipalities.contains(rp)].iloc[0].commune_id
        if id not in best:
            best.append(id)
        if len(best) == 50:
            break
    return best


def kmeans(processed_path, office_dep=None, office_muni=None, exclude=[], verbose=True):
    """
    Return the k-means
    """
    persons_df = pd.read_feather(processed_path+"/persons.feather")
    persons_df = persons_df[persons_df["origin_id"]
                                    != persons_df["destination_id"]]
    persons_df = persons_df[~persons_df.origin_id.isin(exclude)]
    if office_dep:
        persons_df = persons_df[persons_df.origin_id.str[:2].isin(office_dep)]
    if office_muni:
        persons_df = persons_df[persons_df.origin_id.isin(office_muni)]

    df = persons_df.groupby("origin_id").sum()
    municipalities = gpd.read_file(f"{processed_path}/communes.gpkg")
    pop_df = df.merge(municipalities, how="left", left_on="origin_id",
                      right_on="commune_id")[["commune_id", "weight", "x", "y", "geometry"]]
    km = KMeans(n_clusters=50, random_state=1)
    coord = pop_df[["x", "y"]].values
    lbls = pd.Series(km.fit_predict(coord, sample_weight=pop_df["weight"]), name="lbls")

    if verbose:
        print("top_50_kmeans:")
        print(f"  nb_muni: {len(municipalities)}")
        print(f"  nb_classified: {len(lbls[lbls>-1])}")

    df = pop_df[["weight", "geometry"]].join(lbls)
    df = gpd.geodataframe.GeoDataFrame(df).dissolve(by="lbls", aggfunc="sum")
    df = df.sort_values("weight", ascending=False)

    best = []
    for k, v in df.iterrows():
        #use representative point instead of centroid in case of non convex shape
        rp = v.geometry.representative_point()
        id = municipalities[municipalities.contains(rp)].iloc[0].commune_id
        best.append(id)
    return best


def kde(processed_path, office_dep=None, office_muni=None, exclude=[], verbose=True, bandwidth=15000):
    """
    Return top_50 municipalities with highest score on a kernel density estimation
    """
    persons_df = pd.read_feather(processed_path+"/persons.feather")
    persons_df = persons_df[persons_df["origin_id"]
                                    != persons_df["destination_id"]]
    persons_df = persons_df[~persons_df.origin_id.isin(exclude)]
    if office_dep:
        persons_df = persons_df[persons_df.origin_id.str[:2].isin(office_dep)]
    if office_muni:
        persons_df = persons_df[persons_df.origin_id.isin(office_muni)]

    df = persons_df.groupby("origin_id").sum()
    municipalities = gpd.read_file(f"{processed_path}/communes.gpkg")
    pop_df = df.merge(municipalities, how="left", left_on="origin_id",
                      right_on="commune_id")[["commune_id", "weight", "x", "y", "geometry"]]
    coord = pop_df[["x", "y"]].values
    kde = KernelDensity(kernel='gaussian', bandwidth=bandwidth)
    kde.fit(coord, sample_weight=pop_df["weight"])
    kde.score_samples(coord)
    log_dens = kde.score_samples(coord)
    score = pd.Series(np.exp(log_dens), name="score")
    df = pop_df[["commune_id", "geometry"]].join(score)
    df = df.sort_values("score", ascending=False)
    return list(df.commune_id)[:50]


def density_centers(processed_path, office_dep=None, office_muni=None, exclude=[], verbose=True, iso=15):
    """
    Return top_50 municipalities with highest score on a kernel density estimation
    """
    routed_path = processed_path+"/routed.csv"
    routed_df = pd.read_csv(routed_path, sep=";", dtype={"person_id":str,
                                                         "office_id":str,
                                                         "car_travel_time":float,
                                                         "car_distance":float})
    routed_df = routed_df.rename(columns={"person_id":"origin_id",
                        "office_id":"destination_id", "car_distance":"distance"})
    if office_dep:
        routed_df = routed_df[routed_df.origin_id.str[:2].isin(office_dep)]
    if office_muni:
        routed_df = routed_df[routed_df.origin_id.isin(office_muni)]
    routed_df = routed_df.pivot("origin_id", "destination_id", "distance")
    persons_df = pd.read_feather(processed_path+"/persons.feather")
    persons_df = persons_df[persons_df["origin_id"]
                                    != persons_df["destination_id"]]
    persons_df = persons_df[~persons_df.origin_id.isin(exclude)]
    persons_df = persons_df.groupby("origin_id").sum()
    weight = []

    """
    calculating the population in the zone of influence of each muni, population
    in the neighboring munis are added with a factor decreasing with the distance
    """
    for muni, distances in routed_df.iterrows():
        if muni in persons_df.index:
            w = persons_df.loc[muni].weight
        else:
            w=0
        for muni2, d in distances.iteritems():
            if d < iso * 1000: #TODO: should not compare distance with time
                if muni2 in persons_df.index:
                    w += persons_df.loc[muni2].weight / math.log(math.e + d/1000)
        weight.append(w)
    routed_df["weight"]=weight

    # municipalities are sorted by their zone of influence
    routed_df = routed_df.sort_values("weight", ascending=False)
    routed_df = routed_df.drop("weight", axis=1)

    # we iterate through the munis by importance, removing neighboring munis
    to_remove = []
    for muni, distances in routed_df.iterrows():
        if muni not in to_remove:
            to_remove.extend(routed_df[muni][distances<15000].index.drop(muni)) #TODO: replace hardcoded 15000
    return list(routed_df.index.drop(to_remove))[:50]
