import preprocessing.process_hr as hr
import pandas as pd
import numpy as np

def get_hr_population(data_path, departments):
    #Legacy: process HR files
    print("Computing hr population...")
    df = hr.get_population(data_path, departments)
    df["weight"] = 1
    return df.set_index("person_id")

def get_insee_population(data_path, orig_dep=[], dest_dep=[], municipalities=None):
    """
    Reads and filters population data from the given data path based on specified criteria.

    Parameters:
        data_path (str): Path to the directory containing the data file.
        orig_dep (list): List of origin department codes to filter the data by (default=[]).
        dest_dep (list): List of destination department codes to filter the data by (default=[]).
        municipalities (list): List of specific municipalities to include in the data (default=None).

    Returns:
        pandas.DataFrame: A DataFrame containing filtered population data with columns 'origin_id',
        'destination_id', 'weight', and indexed by 'person_id'.
    """
    print("Computing insee population...")
    columns = ["COMMUNE", "ARM", "DCLT", "CS1", "IPONDI", "TRANS", "VOIT"]
    dtype = {"COMMUNE":str, "ARM":str, "DCLT":str, "CS1":str, "IPONDI":float,
             "TRANS":str, "VOIT":str}
    cadres_et_employes = ["3", "4", "5"]
    df = pd.read_csv(f"{data_path}/FD_MOBPRO_2018.csv", sep=";",
                     usecols=columns, dtype=dtype)

    df = df[df["COMMUNE"].str[:2].isin(orig_dep)]
    df = df[df["DCLT"].str[:2].isin(dest_dep)]

    if municipalities:
        df = df[df["COMMUNE"].isin(municipalities)]

    df.COMMUNE.where(~df.COMMUNE.isin(["75056", "69123", "13055"]),
                     df.ARM,
                     inplace=True)
    df = df[df["DCLT"]!=df["COMMUNE"]]
    df = df[df["CS1"].isin(cadres_et_employes)]
    df["has_car"] = pd.to_numeric(df.VOIT, errors="coerce") > 0
    df = df[df.TRANS.isin(["4", "5"])]
    """
    df.TRANS.replace(to_replace="3", value="bike", inplace=True)
    df.TRANS.replace(to_replace=["4", "5"], value="pv", inplace=True)
    df.TRANS.replace(to_replace="6", value="pt", inplace=True)
    """
    df.rename(columns={"COMMUNE":"origin_id",
                       "DCLT": "destination_id",
                       "IPONDI": "weight"}, inplace=True)
    df = df[["origin_id", "destination_id", "weight"]]
    df.dropna(inplace=True)
    df = df.groupby(["origin_id", "destination_id"]).sum().reset_index()
    df["person_id"] = np.arange(len(df))

    return df.set_index("person_id")
