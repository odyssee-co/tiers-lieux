import subprocess as sp
import shutil
import os
import preselection
import pandas as pd
from pathlib import Path
import numpy as np
import preprocessing.communes as communes
import tqdm





def od_shares(data_path):
    """
    return for each couple origin destination the share of car/pt
    """
    df_od = pd.read_csv("%s/%s"%(data_path, "od.csv"), sep = ";",
            dtype = {"origin_id": str, "destination_id": str})


    persons_df = pd.read_csv(data_path+"/processed/persons.csv", dtype=str)
    required_origins = persons_df["origin_id"].unique()
    required_destinations = persons_df["destination_id"].unique()

    top_50 = preselection.get_top_50_municipalities(data_path)
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

    def __init__(self, data_path, population, departments, matsim_conf, preselection=None):
        self.data_path = data_path
        self.population = population
        self.departments = departments
        self.preselection = preselection
        self.matsim_conf = matsim_conf
        self.suffix = str.join('-', departments)

    def compute_request(self):
        path = f"{self.data_path}/processed/request_{self.suffix}.csv"
        if not os.path.isfile(path):
            print("Computing request...")
            municipalities_df = communes.get_communes(self.data_path,
                                                      departments=self.departments)
            origins_df = municipalities_df[municipalities_df.commune_id
                                       .isin(self.population.origin_id.unique())].copy()

            municipalities_df.rename(columns=({"x":"destination_x",
                                               "y":"destination_y",
                                               "commune_id":"office_id"}),
                                               inplace=True)

            requests_df = []
            for index, origin in origins_df.iterrows():
                request_df = municipalities_df.copy()
                request_df["origin_x"] = origin["x"]
                request_df["origin_y"] = origin["y"]
                request_df["person_id"] = origin["commune_id"]
                request_df = request_df[[
                    "person_id", "office_id", "origin_x", "origin_y", "destination_x",
                    "destination_y"]]
                requests_df.append(request_df)
            requests_df = pd.concat(requests_df)
            requests_df.to_csv(path, sep=";", index=False)


    def get_routed(self):
        """
        Call MATSim router
        person_id;office_id;origin_x;origin_y;destination_x;destination_y
        """
        routed_path = f"{self.data_path}/processed/routed_{self.suffix}.csv"
        if not os.path.isfile(routed_path):
            req_path = f"{self.data_path}/processed/request_{self.suffix}.csv"
            if not os.path.isfile(req_path):
                self.compute_request()
            print("Routing...")
            command = [
                shutil.which("java"),
                "-cp", f"{self.data_path}/{self.jar_file}",
                #"-Xmx14G",
                "org.eqasim.odyssee.RunBatchRouting",
                "--config-path", f"{self.data_path}/{self.matsim_conf}",
                "--input-path", req_path,
                "--output-path", routed_path]
            sp.check_call(command, cwd=Path(self.data_path).parent)
        routed_df = pd.read_csv(routed_path, sep=";", dtype={"person_id":str,
                                                             "office_id":str,
                                                             "car_travel_time":float,
                                                             "car_distance":float})
        routed_df.rename(columns={"person_id":"origin_id",
                                  "office_id":"destination_id"},
                                   inplace=True)
        return routed_df


    def get_saved_distance(self, use_modal_share=False, min_saved=10000, isochrone=0, exclude=[]):
        """
        Return a dataframe containing for each employee, the time he would save working
        in each office (0 if the saved time if negative or inferior to min_saved).

        """
        path_saved = f"{self.data_path}/processed/saved_iso{isochrone}_{self.suffix}.csv"
        if os.path.exists(path_saved):
            print("Loading saved distances matrix...")
            saved_df = pd.read_csv(path_saved)
            saved_df.set_index("person_id", inplace=True)
        else:
            routed_df = self.get_routed()
            distance_df = routed_df.pivot(index="origin_id",
                                          columns="destination_id",
                                          values="car_distance")
            baseline_distance = []
            for id, row in self.population.iterrows():
                origin = row["origin_id"]
                destination = row["destination_id"]
                try:
                    baseline_distance.append(distance_df.loc[origin, destination])
                except KeyError:
                    baseline_distance.append(np.nan)
            self.population["baseline_distance"] = baseline_distance
            self.population.dropna(inplace=True)

            if isochrone > 0:
                routed_df.car_distance.where(routed_df.
                                                  car_travel_time<isochrone*60,
                                                  float("inf"), inplace=True)
                distance_df = routed_df.pivot(index="origin_id",
                                              columns="destination_id",
                                              values="car_distance")

            columns = list(distance_df.columns)
            saved_df = pd.DataFrame(columns=columns)
            #self.population = self.population.sample(100) #to_remove
            print("Computing saved distances matrix...")
            for id, row in tqdm.tqdm(self.population.iterrows(),
                                     total=self.population.shape[0]):
                origin = row["origin_id"]
                baseline_distance = row["baseline_distance"]
                distances = distance_df.loc[origin].copy()
                distances = baseline_distance - distances
                distances.name = id
                saved_df = saved_df.append(distances)
            saved_df.index.names = ['person_id']
            saved_df.to_csv(path_saved)

        saved_df.columns = saved_df.columns.astype(str)
        saved_df.drop(columns=exclude, inplace=True)
        if preselection:
            saved_df = saved_df[self.preselection]
        saved_df = saved_df.where(saved_df > min_saved, 0)
        print(saved_df.shape)
        return saved_df
