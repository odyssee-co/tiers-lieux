import geopandas as gpd

def get_coord(df_persons, communes):
    """
    get origin and destination coordinates
    df_persons: origin_id, destination_id
    communes: commune_id, x, y
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

def get_communes(data_path):
    """
    return geo dataFrame with communes names, ids, geometry, and coordinates (x,y)
    df_communes: nom, commune_id, geometry, x, y
    """
    df_communes = gpd.read_file(data_path+"iris/communes-20210101.shp")
    df_communes.geometry = df_communes.geometry.to_crs(2154)
    df_communes["x"] = df_communes.geometry.centroid.x
    df_communes["y"] = df_communes.geometry.centroid.y
    from IPython import embed; embed()
    df_communes = df_communes[["nom","insee", "geometry","x","y"]]
    df_communes = df_communes.rename(columns={"insee": "commune_id"})
    df_communes["commune_id"] = df_communes["commune_id"].astype(str)
    return df_communes
