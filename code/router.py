import subprocess as sp
import shutil
import os
import pandas as pd
from pathlib import Path
import preprocessing.communes as communes
import tqdm


class Router:

    jar_file = "flow-1.2.0.jar"

    def __init__(self, data_path, suffix, population, departments, matsim_conf, preselection=None):
        self.data_path = data_path
        self.population = population
        self.departments = departments
        self.preselection = preselection
        self.matsim_conf = matsim_conf
        self.suffix_dep = str.join('-', departments)
        self.suffix = f"{suffix}_{self.suffix_dep}"

    def compute_request(self):
        path = f"{self.data_path}/processed/request_{self.suffix_dep}.csv"
        if not os.path.isfile(path):
            print("Computing request...")
            municipalities_df = communes.get_communes(self.data_path,
                                                      departments=self.departments)
            #origins_df = municipalities_df[municipalities_df.commune_id
            #                           .isin(self.population.origin_id.unique())].copy()
            origins_df = municipalities_df.copy()
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
        routed_path = f"{self.data_path}/processed/routed_{self.suffix_dep}.csv"
        if not os.path.isfile(routed_path):
            req_path = f"{self.data_path}/processed/request_{self._suffix_dep}.csv"
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


    def get_saved_distance(self, use_modal_share=False, min_saved=10,
                            isochrone=0, exclude=[]):
        """
        Return a dataframe containing for each employee, the time he would save working
        in each office (0 if the saved time if negative or inferior to min_saved).

        """
        isochrone *= 60
        min_saved *= 60
        path_saved = f"{self.data_path}/processed/saved{self.suffix}.feather"
        if os.path.exists(path_saved):
            print("Loading saved distances matrix...")
            saved_df = pd.read_feather(path_saved).set_index("person_id")
        else:
            print("Processing saved distances matrix")
            routed_df = self.get_routed()
            routed_df = routed_df[routed_df["origin_id"].isin(self.population.origin_id)]
            if self.preselection:
                offices_id = self.preselection
            else:
                offices_id = routed_df["destination_id"].unique()
            routed_df.set_index(["origin_id", "destination_id"], inplace=True)

            #calculate baseline car distance and check if user uses car anyway
            saved_df = pd.DataFrame()
            #self.population = self.population.sample(100) #to_remove
            for id, row in tqdm.tqdm(self.population.iterrows(),
                                     total=self.population.shape[0]):
                origin, reg_office, weight = row
                b_ct, b_cd, b_ptt, b_ptd = routed_df.loc[origin, reg_office]
                saved = {"weight":weight}
                for office in offices_id:
                    ct, cd, ptt, ptd = routed_df.loc[origin, office]
                    saved_dist = 0
                    uses_car =  b_ct > b_ptt #used to go by car even if better pt existed
                    car_best = ct < ptt
                    #will the user keep using car and change office?
                    if uses_car or car_best:
                        if ct < isochrone and b_ct - ct > min_saved:
                            saved_dist = (b_cd - cd) * weight
                    #or switch to pt?
                    else:
                        if b_ct - ptt > min_saved:
                            saved_dist = b_cd * weight
                    saved[office] = saved_dist
                saved = pd.Series(saved, name=id)
                saved_df = saved_df.append(saved)
            saved_df.index.names = ["person_id"]
            saved_df.reset_index().to_feather(path_saved)

        if not self.preselection:
            saved_df.drop(columns=exclude, inplace=True)
        return saved_df
