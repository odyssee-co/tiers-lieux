import subprocess as sp
import shutil
import os
import pandas as pd
from pathlib import Path
import preselection
import tqdm
import geopandas as gpd

class Router:

    jar_file = "flow-1.2.0.jar"

    def __init__(self, data_path, processed_path, exclude, matsim_conf):
        self.data_path = data_path
        self.processed_path = processed_path
        self.exclude = exclude
        self.matsim_conf = matsim_conf

    def compute_request(self):
        path = f"{self.processed_path}/request.csv"
        if not os.path.isfile(path):
            print("Computing request...")
            municipalities_df = gpd.read_file(f"{self.processed_path}/communes.gpkg",
                                              dtype={"commune_id":str})

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
        routed_path = f"{self.processed_path}/routed.csv"
        if not os.path.isfile(routed_path):
            req_path = f"{self.processed_path}/request.csv"
            if not os.path.isfile(req_path):
                self.compute_request()
            print("Routing...")
            command = [
                shutil.which("java"),
                "-cp", f"{self.data_path}/{self.jar_file}",
                "-Xmx28G",
                "org.eqasim.odyssee.RunBatchRouting",
                "--config-path", self.matsim_conf,
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

    def get_routed_intra(self):
        """
        Add estimation of the traveled distances and times if the origin
        municipality is the same than the destination municipality
        """
        routed_intra_path = f"{self.processed_path}/routed_intra.feather"
        if not os.path.isfile(routed_intra_path):
            routed_df = self.get_routed()
            municipalities_df = gpd.read_file(f"{self.processed_path}/communes.gpkg",
                                                  dtype={"commune_id":str})
            routed_df.loc[routed_df.origin_id==routed_df.destination_id,
                            "car_distance"]=municipalities_df.avg_d_intra.values
            routed_df.loc[routed_df.origin_id==routed_df.destination_id,
                   "car_travel_time"]=municipalities_df.avg_d_intra.values*1000/3600
            routed_df.loc[routed_df.origin_id==routed_df.destination_id,
                            "pt_distance"]=municipalities_df.avg_d_intra.values
            routed_df.loc[routed_df.origin_id==routed_df.destination_id,
                   "pt_travel_time"]=municipalities_df.avg_d_intra.values*1000/3600
            routed_df.reset_index(drop=True).to_feather(routed_intra_path)
        else:
            routed_df = pd.read_feather(routed_intra_path)
        return routed_df


    def get_saved_distance(self, isochrone, min_saved, presel_func):
        """
        Return a dataframe containing for each employee, the time he would save working
        in each office (0 if the saved time if negative or inferior to min_saved).
        """
        exclude = self.exclude
        path_saved = f"{self.processed_path}/saved_iso{isochrone}_min{min_saved}_{presel_func}.feather"
        if os.path.exists(path_saved):
            print(f"Loading matrix ({isochrone}, {min_saved}, {presel_func})...")
            saved_df = pd.read_feather(path_saved).set_index("person_id")
        else:
            print(f"Processing matrix ({isochrone}, {min_saved}, {presel_func})...")
            isochrone *= 60
            min_saved *= 60
            routed_df = self.get_routed_intra()

            population = pd.read_feather(f"{self.processed_path}/persons.feather")
            #routed_df = routed_df[routed_df["origin_id"].isin(population.origin_id)]
            """
            from IPython import embed; embed()
            municipalities_df = gpd.read_file(
                                        f"{self.processed_path}/communes.gpkg",
                                        dtype={"commune_id":str})
            municipalities_df["intra"] = municipalities_df["geometry"].apply(intra_car_travel_distance)
            df = routed_df[routed_df["origin_id"]==routed_df["destination_id"]]
            """
            if presel_func:
                args = [self.processed_path, exclude]
                presel_func = presel_func.split("*")
                for a in presel_func[1:]:
                    args.append(a)
                offices_id = getattr(preselection, f"{presel_func[0]}")(*args)
            else:
                offices_id = population.origin_id.unique()
            routed_df.set_index(["origin_id", "destination_id"], inplace=True)

            #calculate baseline car distance and check if user uses car anyway
            saved_df = pd.DataFrame()
            for id, row in tqdm.tqdm(population.iterrows(),
                                     total=population.shape[0]):
                origin, reg_office, weight = row
                b_ct, b_cd, b_ptt, b_ptd = routed_df.loc[origin, reg_office]
                saved = {"weight":weight}
                for office in offices_id:
                    ct, cd, ptt, ptd = routed_df.loc[origin, office]
                    saved_dist = 0
                    uses_car =  b_ct > b_ptt #used to go by car even if better pt existed
                    car_best = ct <= ptt # <= so we take in account the intra_communal trips
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

        return saved_df
