import pandas as pd
import geopandas

def get_coord(df_persons, communes):
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
    return dataFrame with communes names, ids, postal codes, and coordinates (x,y)
    """
    df_communes = pd.read_csv(data_path+"/code-postal-code-insee-2015.csv", sep=";")
    df_communes[["x","y"]] = df_communes["Geo Point"].str.split(",", expand=True)
    df_communes = df_communes[["NOM_COM","INSEE_COM", "Code_postal","x","y"]]
    #df_communes = df_communes.drop_duplicates("Code_postal") #TODO keep biggest pop
    df_communes = df_communes.rename(columns={"NOM_COM": "nom",
        "INSEE_COM": "commune_id", "Code_postal": "postal_id"})
    df_communes["commune_id"] = df_communes["commune_id"].astype(str)
    return df_communes

def to_gdf(df_communes):
    """
    return a geopandas df from a df with x and y
    """
    gdf_communes = geopandas.GeoDataFrame(
        df_communes, geometry=geopandas.points_from_xy(df_communes.x, df_communes.y))
    return gdf_communes
    #gdf_communes.to_file(data_path+"/processed/communes.gpkg", driver = "GPKG")

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
