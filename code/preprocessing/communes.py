import geopandas as gpd
import pandas as pd
from shapely.geometry import Point
import random
import numpy as np

def get_coord(df_persons, communes):
    """
    Get origin and destination coordinates for persons based on given communes data.

    Parameters:
        df_persons (pandas.DataFrame): DataFrame with 'origin_id' and 'destination_id'.
        communes (pandas.DataFrame): DataFrame with 'commune_id', 'x', and 'y' columns.

    Returns:
        pandas.DataFrame: DataFrame with 'origin_x', 'origin_y', 'destination_x', and 'destination_y'
        columns added to df_persons.
    """
    communes = communes.drop_duplicates("commune_id")
    communes = communes[["commune_id", "x", "y"]]
    df_persons = df_persons.merge(communes.rename(columns={
                  "commune_id":"origin_id", "x": "origin_x", "y": "origin_y"}),
                   on="origin_id", how="left")
    df_persons = df_persons.merge(communes.rename(columns={
                  "commune_id":"destination_id", "x": "destination_x", "y": "destination_y"}),
                   on="destination_id", how="left")
    #df_persons.to_csv(data_path+"/processed/od_al.csv", sep=";", index=False)
    return df_persons

def avg_d_within(poly, nb_it):
    """
    Calculate the average distance between random points within a polygon.

    Parameters:
        poly (shapely.geometry.Polygon): Polygon object.
        nb_it (int): Number of iterations to calculate the average distance.

    Returns:
        float: Average distance between random points within the polygon.
    """
    min_x, min_y, max_x, max_y = poly.bounds
    sum = 0
    for i in range(nb_it):
        points = []
        while len(points) < 2:
            random_point = Point([random.uniform(min_x, max_x), random.uniform(min_y, max_y)])
            if (random_point.within(poly)):
                points.append(random_point)
        sum += points[0].distance(points[1])
    return sum/nb_it

def get_communes(data_path, departments=[]):
    """
    Read and process municipality data, returning a GeoDataFrame with commune names, IDs, geometry, and coordinates.

    Parameters:
        data_path (str): Path to the directory containing the municipality shapefile.
        departments (list): List of department codes to filter the data by (default=[]).

    Returns:
        geopandas.GeoDataFrame: GeoDataFrame with columns 'nom' (name), 'commune_id', 'geometry', 'x', 'y',
        and 'avg_d_intra' (average intra-municipality distance) after processing.
    """
    print("Processing municipalities...")
    df_communes = gpd.read_file(data_path+"/iris/communes-20220101.shp", dtype={"insee":str})
    df_communes = df_communes[["nom", "insee", "geometry"]]
    """
    arn_path = data_path+"/arrondissements.csv"
    df_arrondissements = gpd.GeoDataFrame(pd.read_csv(arn_path, dtype={"insee":str}))
    df_arrondissements = df_arrondissements[["nom", "insee", "geometry"]]
    df_communes = gpd.GeoDataFrame(pd.concat([df_communes, df_arrondissements]))
    """
    df_communes["department"] = df_communes["insee"].str[:2]
    df_communes = df_communes[df_communes["department"].isin(departments)]
    df_communes.geometry = df_communes.geometry.to_crs(2154)
    df_communes["x"] = df_communes.geometry.centroid.x
    df_communes["y"] = df_communes.geometry.centroid.y
    df_communes = df_communes[["nom","insee", "geometry","x","y"]]
    df_communes = df_communes.rename(columns={"insee": "commune_id"})
    avg_d_intra = []
    for k, v in df_communes.iterrows():
        avg_d_intra.append(avg_d_within(v.geometry, 1000))
    df_communes["avg_d_intra"] = np.array(avg_d_intra)
    return df_communes


def get_insee_name(data_path):
    df_names = pd.read_excel(data_path+"/reference_IRIS_geo2017.xls", skiprows=5)
    df_names["office_id"] = df_names["CODE_IRIS"].astype(str).str[:5]
    df_names["label"] = df_names["LIBCOM"].str.upper()
    df_names = df_names[["office_id", "label"]]
    df_names = df_names.drop_duplicates("office_id")
    return df_names

def get_insee_postal(data_path):
    df_conversion = pd.read_csv(data_path+"/code-postal-code-insee-2015.csv", sep=";")
    df_conversion = df_conversion[["INSEE_COM", "Code_postal"]]
    df_conversion = df_conversion.rename(columns={
        "INSEE_COM": "commune_id", "Code_postal": "postal_id"
    })[["commune_id", "postal_id"]]
    df_conversion = df_conversion.drop_duplicates("postal_id")
    df_conversion = df_conversion.dropna()
    df_conversion["commune_id"] = df_conversion["commune_id"].astype(str)
    df_conversion["postal_id"] = df_conversion["postal_id"].astype(int)
    df_conversion["postal_id"] = df_conversion["postal_id"].astype(str)
    return df_conversion
