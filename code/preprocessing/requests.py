import preprocessing.process_hr as hr
import preprocessing.communes as com
import pandas as pd
import geopandas as gpd
import numpy as np
import os

def compute_initial_requests(data_path):
    if not os.path.isfile("%s/processed/initial_request.csv"%data_path):
        print("Computing initial request...")
        communes_df = com.get_communes(data_path)
        communes_df.to_file(data_path+"/processed/communes.gpkg", driver = "GPKG")

        al_df = hr.process_action_logement(data_path, communes_df)
        #al_df.to_csv(data_path+"/processed/od_al.csv", sep=";", index=False)
        al_df = al_df[["origin_id", "destination_id"]]

        met_df = hr.process_metropole(data_path)
        #met_df.to_csv(data_path+"/processed/od_metropole.csv", sep=";", index=False)
        met_df = met_df[["origin_id", "destination_id"]]

        reg_df = hr.process_region(data_path)
        #reg_df.to_csv(data_path+"/processed/od_region.csv", index=False)
        reg_df = reg_df[["origin_id", "destination_id"]]

        persons_df = pd.concat([al_df, met_df, reg_df])
        persons_df = com.get_coord(persons_df, communes_df)
        persons_df["person_id"] = np.arange(len(persons_df))
        persons_df.to_csv(data_path+"/processed/persons.csv", index=False)
        persons_df["office_id"] = persons_df["destination_id"]
        persons_df = persons_df[["person_id", "office_id", "origin_x", "origin_y",
                                    "destination_x", "destination_y"]]
        persons_df.dropna(inplace=True)
        persons_df.to_csv(data_path+"/processed/initial_request.csv", sep=";", index=False)


def get_top_50_offices(data_path):
    """
    return the top 50 communes in midi-pyrénnées with the most inhabitants
    leaving every days to go to work in another communes
    """
    persons_df = pd.read_csv(data_path+"/processed/persons.csv")
    persons_df = persons_df[persons_df["origin_id"].str[0:2].isin(
                             ["09", "12", "31", "32", "46", "65", "81", "82"])]
    persons_df = persons_df[persons_df["origin_id"].astype(str)
                                    != persons_df["destination_id"].astype(str)]
    top_50 = list(persons_df["origin_id"].value_counts()[0:50].index)
    return top_50


def compute_offices_request(data_path, offices_file=None):
    if not os.path.isfile("%s/processed/offices_request.csv"%data_path):
        print("Computing offices request...")
        persons_df = pd.read_csv(data_path+"/processed/initial_request.csv", sep=";")
        communes_df = gpd.read_file(data_path+"/processed/communes.gpkg")

        if offices_file:
            offices = []
            with open("%s/%s"%(data_path, offices_file)) as f:
                for line in f:
                    offices.append(line.strip())
        else:
            offices = get_top_50_offices(data_path)
        offices_df = communes_df[communes_df["commune_id"].isin(offices)]
        offices_df = offices_df.rename(columns={"commune_id":"office_id"})
        offices_df = offices_df[["office_id", "x", "y"]]

        requests_df = []
        for index, office in offices_df.iterrows():
            request_df = persons_df.copy()
            request_df["destination_x"] = office["x"]
            request_df["destination_y"] = office["y"]
            request_df["office_id"] = office["office_id"]
            request_df = request_df[[
                "person_id", "office_id", "origin_x", "origin_y", "destination_x",
                "destination_y"]]
            requests_df.append(request_df)

        requests_df = pd.concat(requests_df)
        requests_df.to_csv(data_path+"/processed/offices_request.csv", sep=";", index=False)
