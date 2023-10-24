import subprocess as sp
import shutil
import os
import pandas as pd
from pathlib import Path
import preselection
import tqdm
import geopandas as gpd

#TODO: replace the eqasim router used to calculate the time and distance matrices by the mobility referential

class Router:
    """
    A class representing a router for transportation simulations.

    Attributes:
        jar_file (str): Path to the .jar file for running transportation simulations.
        data_path (str): Path to the directory containing input data files.
        processed_path (str): Path to the directory where processed data will be stored.
        matsim_conf (str): Path to the MATSim configuration file.
    """

    def __init__(self, data_path, processed_path, matsim_conf):
        """
        Initializes a Router object with the given data paths and MATSim configuration file path.

        Parameters:
            data_path (str): Path to the directory containing input data files.
            processed_path (str): Path to the directory where processed data will be stored.
            matsim_conf (str): Path to the MATSim configuration file.
        """
        self.jar_file = "equasim-java/flow/target/flow-1.2.0.jar"
        self.data_path = data_path
        self.processed_path = processed_path
        self.matsim_conf = matsim_conf

    def compute_request(self):
        """
        Compute eqasim csv request file if it doesn't already exist.
        """
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
        Call eqasim router to compute routed data based on request data.

        If the routed data file does not exist, it computes the routing using MATSim.
        The function assumes the existence of request data and specific columns in the CSV file.

        Returns:
        pandas.DataFrame: DataFrame containing routed data with columns 'origin_id', 'destination_id',
        'car_travel_time', and 'car_distance'.
        """
        routed_path = f"{self.processed_path}/routed.csv"
        if not os.path.isfile(routed_path):
            req_path = f"{self.processed_path}/request.csv"
            if not os.path.isfile(req_path):
                self.compute_request()
            print("Routing...")
            command = [
                shutil.which("java"),
                "-cp", self.jar_file,
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
        municipality is the same as the destination municipality.

        Computes and saves the routed data with intra-municipality distances and times if not already done.
        Assumes the existence of routed data and specific columns in the input data files.

        Returns:
        pandas.DataFrame: DataFrame containing routed data with updated 'car_distance',
        'car_travel_time', 'pt_distance', and 'pt_travel_time' columns.
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


    def get_saved_distance(self, isochrone, min_saved, presel_func, office_dep,
                           office_muni, vacancy_file, exclude):
        """
        Calculate for each employee, the time he would save working in each office.

        Parameters:
            isochrone (int): Isochrone duration in minutes.
            min_saved (int): Minimum saved time in minutes to consider an office.
            presel_func (str): Preselection function name.
            office_dep (str): Department.
            office_muni (list): List of municipality IDs for office selection.
            vacancy_file (str): Path to the vacancy file.
            exclude (list): List of municipalities to be excluded from office selection.

        Returns:
            pd.DataFrame: A dataframe containing time saved by each employee for each office.
                          Columns represent office IDs, and rows represent employee IDs.
                          Time saved is 0 if it's negative or less than min_saved.
        """
        path_saved = f"{self.processed_path}/saved_iso{isochrone}_min{min_saved}_{presel_func}.feather"
        if os.path.exists(path_saved):
            print(f"Loading matrix ({isochrone}, {min_saved}, {presel_func})...")
            saved_df = pd.read_feather(path_saved).set_index("person_id")
        else:
            print(f"Processing matrix ({isochrone}, {min_saved}, {presel_func})...")
            isochrone *= 60
            min_saved *= 60
            routed_df = self.get_routed_intra()
            routed_df.set_index(["origin_id", "destination_id"], inplace=True)

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
            if vacancy_file:
                vacancy_df = pd.read_feather(vacancy_file)
                office_muni = list(vacancy_df.idcom.unique())

            #calling the preselection function
            args = [self.processed_path, office_dep, office_muni, exclude]
            presel_func = presel_func.split("*")
            for a in presel_func[1:]:
                args.append(a)
            offices_id = getattr(preselection, f"{presel_func[0]}")(*args)

            #calculate baseline car distance and check if user uses car anyway
            saved_df = []
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
                saved = pd.Series(saved, name=str(id))
                saved_df.append(saved)
            saved_df = pd.DataFrame(saved_df)
            saved_df.index.names = ["person_id"]
            saved_df.reset_index().to_feather(path_saved)

        return saved_df
