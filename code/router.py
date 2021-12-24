import subprocess as sp
import shutil
import os
import preprocessing.requests as req
import pandas as pd
from pathlib import Path


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
        "-cp", self.data_path + self.jar_file,
        #"-Xmx14G",
        "org.eqasim.odyssee.RunBatchRouting",
        "--config-path", self.data_path + conf_file,
        "--input-path", self.data_path + requests_file,
        "--output-path", self.data_path + "/processed/" + output_file
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


    def get_saved_distance(self):
        """
        return a dataframe containing for each employee, the time he would save working
        in each office (0 if the saved time if negative)
        """
        routed_inital = self.get_routed_initial()
        routed_offices = self.get_routed_office()
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
