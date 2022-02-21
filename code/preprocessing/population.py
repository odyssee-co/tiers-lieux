import preprocessing.process_hr as hr
import pandas as pd
import numpy as np
import os

def get_hr_population(data_path, departments):
    path = f"{data_path}/processed/persons.csv"
    if os.path.isfile(path):
        print("Loading hr population...")
        df = pd.read_csv(path, dtype={"origin_id":str, "destination_id":str})
    else:
        print("Computing hr population...")
        df = hr.get_population(data_path, departments)
        df["weight"] = 1
        df["mode"] = "pv"
        df["has_car"] = True
        df.to_csv(path, index=False)
    return df.set_index("person_id")

def get_insee_population(data_path, departments):
    path = f"{data_path}/processed/persons.csv"
    if os.path.exists(path):
        print("Loading insee population...")
        df = pd.read_csv(path, dtype={"origin_id":str, "destination_id":str})
    else:
        print("Computing insee population...")
        columns = ["COMMUNE", "DCLT", "CS1", "IPONDI", "TRANS", "VOIT"]
        dtype = {"COMMUNE":str, "DCLT":str, "CS1":str, "IPONDI":float, "TRANS":str,
                 "VOIT":str}
        cadres_et_employes = ["3", "4", "5"]
        df = pd.read_csv(f"{data_path}/FD_MOBPRO_2018.csv", sep=";",
                         usecols=columns, dtype=dtype)
        df = df[df["COMMUNE"].str[:2].isin(departments)]
        df = df[df["DCLT"].str[:2].isin(departments)]
        df = df[df["CS1"].isin(cadres_et_employes)]
        df["has_car"] = pd.to_numeric(df.VOIT, errors="coerce") > 0
        df = df[df.TRANS.isin(["3", "4", "5", "6"])]
        df.TRANS.replace(to_replace="3", value="bike", inplace=True)
        df.TRANS.replace(to_replace=["4", "5"], value="pv", inplace=True)
        df.TRANS.replace(to_replace="6", value="pt", inplace=True)
        df.rename(columns={"COMMUNE":"origin_id",
                           "DCLT": "destination_id",
                           "IPONDI": "weight",
                           "TRANS": "mode"}, inplace=True)
        df = df[["origin_id", "destination_id", "weight", "mode", "has_car"]]
        df.dropna(inplace=True)
        df["person_id"] = np.arange(len(df))
        df.to_csv(path, index=False)
    return df.set_index("person_id")
