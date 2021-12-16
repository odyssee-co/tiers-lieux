import preprocessing.process_hr as hr
import preprocessing.communes as com
import pandas as pd
import geopandas as gpd
import numpy as np
import os
import router
import optimizer

def compute_initial_requests(data_path):
    if not os.path.isfile("%s/processed/initial_request.csv"%data_path):
        print("Computing initial request...")
        communes = com.get_communes(data_path)
        communes.to_file(data_path+"/processed/communes.gpkg", driver = "GPKG")

        al_df = hr.process_action_logement(data_path, communes)
        #al_df.to_csv(data_path+"/processed/od_al.csv", sep=";", index=False)
        al_df = al_df[["origin_id", "destination_id"]]

        met_df = hr.process_metropole(data_path)
        #met_df.to_csv(data_path+"/processed/od_metropole.csv", sep=";", index=False)
        met_df = met_df[["origin_id", "destination_id"]]

        reg_df = hr.process_region(data_path)
        #reg_df.to_csv(data_path+"/processed/od_region.csv", index=False)
        reg_df = reg_df[["origin_id", "destination_id"]]

        persons_df = pd.concat([al_df, met_df, reg_df])
        persons_df = com.get_coord(persons_df, communes)
        persons_df["person_id"] = np.arange(len(persons_df))
        persons_df.to_csv(data_path+"/processed/persons.csv", index=False)
        persons_df["office_id"] = persons_df["destination_id"]
        persons_df = persons_df[["person_id", "office_id", "origin_x", "origin_y",
                                    "destination_x", "destination_y"]]
        persons_df.dropna(inplace=True)
        persons_df.to_csv(data_path+"/processed/initial_request.csv", sep=";", index=False)

def compute_offices_request(data_path, offices_file):
    if not os.path.isfile("%s/processed/offices_request.csv"%data_path):
        print("Computing offices request...")
        persons = pd.read_csv(data_path+"/processed/initial_request.csv", sep=";")
        communes = gpd.read_file(data_path+"/processed/communes.gpkg")

        offices = []
        with open("%s/%s"%(data_path, offices_file)) as f:
            for line in f:
                offices.append(line.strip())
        offices_df = communes[communes["commune_id"].isin(offices)]
        offices_df = offices_df.rename(columns={"commune_id":"office_id"})
        offices_df = offices_df[["office_id", "x", "y"]]

        requests_df = []
        for index, office in offices_df.iterrows():
            request_df = persons.copy()
            request_df["destination_x"] = office["x"]
            request_df["destination_y"] = office["y"]
            request_df["office_id"] = office["office_id"]
            request_df = request_df[[
                "person_id", "office_id", "origin_x", "origin_y", "destination_x",
                "destination_y"]]
            requests_df.append(request_df)

        requests_df = pd.concat(requests_df)
        requests_df.to_csv(data_path+"/processed/offices_request.csv", sep=";", index=False)


def get_routed_initial():
    routed_initial_path = "%s/processed/routed_initial.csv"%data_path
    if not os.path.isfile(routed_initial_path):
        compute_initial_requests(data_path)
        router.run(data_path, "/processed/initial_request.csv",
                "/matsim-conf/toulouse_config.xml", "routed_initial.csv")
    return pd.read_csv(routed_initial_path, sep=";")

def get_routed_office():
    routed_offices_path = "%s/processed/routed_offices.csv"%data_path
    if not os.path.isfile(routed_offices_path):
        compute_offices_request(data_path, offices_file)
        router.run(data_path, "/processed/offices_request.csv",
                "/matsim-conf/toulouse_config.xml", "routed_initial.csv")
    return pd.read_csv(routed_offices_path, sep=";")

def get_saved_distance():
    routed_inital = get_routed_initial()
    routed_offices = get_routed_office()
    routed_inital = routed_inital.rename(columns={
        "office_id" : "original_office",
        "car_travel_time" : "baseline_car_travel_time",
        "car_distance" : "baseline_car_distance",
        "pt_travel_time" : "baseline_pt_travel_time",
        "pt_distance" : "baseline_pt_distance",
    })
    df = pd.merge(routed_inital, routed_offices, on="person_id", how="left")
    df["saved_travel_distance"] = df["baseline_car_distance"] - df["car_distance"]
    saved_df = df.pivot(index="person_id", columns="office_id", values="saved_travel_distance")
    saved_df = saved_df.where(saved_df > 0, 0)
    return saved_df



if __name__ == "__main__":
    #from IPython import embed; embed()
    data_path = "/home/matt/git/tiers-lieux/data/"
    offices_file = "top50.txt"
    saved_df = get_saved_distance()
    optimizer.brute_force(saved_df)
