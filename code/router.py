import subprocess as sp
import shutil
import os
import preprocessing.requests as req
import pandas as pd
from pathlib import Path
import numpy as np
import preprocessing.communes as communes

def get_matrix(data_path):
    path = f"{data_path}/all_request.csv"
    if not os.path.isfile(path):
        departments = ["09", "11", "31", "32", "81", "82"]
        municipalities_df = communes.get_communes(data_path, departments=departments)
        municipalities_df.rename(columns=({"x":"origin_x",
                                           "y":"origin_y",
                                           "commune_id":"person_id"}),
                                           inplace=True)
        requests_df = []
        for index, office in municipalities_df.iterrows():
            request_df = municipalities_df.copy()
            request_df["destination_x"] = office["origin_x"]
            request_df["destination_y"] = office["origin_y"]
            request_df["office_id"] = office["person_id"]
            request_df = request_df[[
                "person_id", "office_id", "origin_x", "origin_y", "destination_x",
                "destination_y"]]
            requests_df.append(request_df)
        requests_df = pd.concat(requests_df)
        requests_df.to_csv(data_path+"/all_request.csv", sep=";", index=False)
    r = Router(data_path)
    r.run("all_request.csv", "/matsim-conf/toulouse_config.xml", "routed_all.csv")




def od_shares(data_path):
    """
    return for each couple origin destination the share of car/pt
    """
    df_od = pd.read_csv("%s/%s"%(data_path, "od.csv"), sep = ";",
            dtype = {"origin_id": str, "destination_id": str})


    persons_df = pd.read_csv(data_path+"/processed/persons.csv", dtype=str)
    required_origins = persons_df["origin_id"].unique()
    required_destinations = persons_df["destination_id"].unique()

    top_50 = req.get_top_50_municipalities(data_path)
    required_destinations = np.concatenate((required_destinations, top_50))

    df_od = df_od[df_od["origin_id"].isin(required_origins)]
    df_od = df_od[df_od["destination_id"].isin(required_destinations)]
    df_od = df_od.sort_values(by=["origin_id", "destination_id", "commute_mode"])

    df_od["mode"] = "other"
    df_od.loc[df_od["commute_mode"] == "car", "mode"] = "car"
    df_od.loc[df_od["commute_mode"] == "pt", "mode"] = "pt"


    df_shares = pd.pivot_table(df_od, values="weight", index=[
                               "origin_id", "destination_id"], columns=["mode"])
    df_shares["total"] = df_shares["car"] + df_shares["pt"] + df_shares["other"]
    df_shares["share_car"] = df_shares["car"] / df_shares["total"]
    df_shares["share_pt"] = df_shares["pt"] / df_shares["total"]

    # When we have no data, we assume the commuter will use the car
    df_shares.loc[df_shares["total"] == 0.0, "share_car"] = 1
    df_shares.loc[df_shares["total"] == 0.0, "share_pt"] = 0
    df_shares = df_shares[["share_car", "share_pt"]].reset_index()
    return df_shares


class Router:

    jar_file = "flow-1.2.0.jar"

    def __init__(self, data_path):
        self.data_path = data_path


    def run(self, requests_file, conf_file, output_file, return_flows=False):
        """
        read df_requests from csv and call MATSim router
        person_id;office_id;origin_x;origin_y;destination_x;destination_y
        """
        print("Routing %s..."%requests_file)
        command = [
        shutil.which("java"),
        "-cp", "%s/%s"%(self.data_path, self.jar_file),
        #"-Xmx14G",
        "org.eqasim.odyssee.RunBatchRouting",
        "--config-path", "%s/%s"%(self.data_path, conf_file),
        "--input-path", "%s/%s"%(self.data_path, requests_file),
        "--output-path", "%s/processed/%s"%(self.data_path, output_file)
        ]
        if return_flows:
            command += [
            "--flow-output-path", "flows.csv"
            ]
        sp.check_call(command, cwd=Path(self.data_path).parent)


    def get_routed_initial(self):
        """
        return a dataframe with the travel time for each employee to his original office
        "office_id", "car_travel_time", "car_distance", "pt_travel_time", "pt_distance"
        """
        routed_initial_path = "%s/processed/routed_initial.csv"%self.data_path
        if not os.path.isfile(routed_initial_path):
            req.compute_initial_requests(self.data_path)
            self.run("/processed/initial_request.csv",
                    "/matsim-conf/toulouse_config.xml", "routed_initial.csv")
        return pd.read_csv(routed_initial_path, sep=";")


    def get_routed_office(self):
        """
        return a dataframe with the travel time for each employees to each office
        "office_id", "car_travel_time", "car_distance", "pt_travel_time", "pt_distance"
        """
        routed_offices_path = "%s/processed/routed_offices.csv"%self.data_path
        if not os.path.isfile(routed_offices_path):
            req.compute_offices_request(self.data_path)
            self.run("/processed/offices_request.csv",
                    "/matsim-conf/toulouse_config.xml", "routed_offices.csv")
        return pd.read_csv(routed_offices_path, sep=";")


    def get_saved_distance(self, use_modal_share=False, min_saved=10000, isochrone=0):
        """
        Return a dataframe containing for each employee, the time he would save working
        in each office (0 if the saved time if negative or inferior to min_saved).

        """
        routed_inital = self.get_routed_initial()
        routed_offices = self.get_routed_office()
        if isochrone > 0:
            routed_offices.car_distance.where(routed_offices.
                                              car_travel_time<isochrone*60,
                                              float("inf"), inplace=True)
        routed_inital = routed_inital.rename(columns={
            "office_id" : "original_office",
            "car_travel_time" : "baseline_car_travel_time",
            "car_distance" : "baseline_car_distance",
            "pt_travel_time" : "baseline_pt_travel_time",
            "pt_distance" : "baseline_pt_distance",
        })
        df = pd.merge(routed_inital, routed_offices, on="person_id", how="left")

        if use_modal_share:
            #We weight the car distance by the modal shares
            persons_path = self.data_path+"/processed/persons.csv"
            persons_df = pd.read_csv(persons_path)[["person_id", "origin_id"]]
            df = pd.merge(df, persons_df, on="person_id", how="left")
            df["origin_id"] = df["origin_id"].astype("str")
            df["original_office"] = df["original_office"].astype("str")
            df["office_id"] = df["office_id"].astype("str")
            modal_shares = od_shares(self.data_path)
            df = pd.merge(df, modal_shares.rename(
                          columns={
                          "destination_id":"original_office",
                          "share_car":"share_car_orig"}),
                          on=["origin_id", "original_office"],
                          how="left")
            df = pd.merge(df, modal_shares.rename(
                          columns={
                          "destination_id":"office_id",
                          "share_car":"share_car_new"}),
                          on=["origin_id", "office_id"],
                          how="left")
            df["baseline_car_distance"] *= df["share_car_orig"]
            df["car_distance"] *= df["share_car_new"]

        df["saved_travel_distance"] = df["baseline_car_distance"] - df["car_distance"]
        saved_df = df.pivot(index="person_id", columns="office_id", values="saved_travel_distance")
        saved_df = saved_df.where(saved_df > min_saved, 0)
        saved_df.columns = saved_df.columns.astype(str)
        return saved_df
