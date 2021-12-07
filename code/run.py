import preprocessing.process_hr as hr
import preprocessing.communes as com
import pandas as pd
import geopandas as gpd
import numpy as np
import router


def compute_initial_requests(data_path):
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
    persons_df["office_id"] = persons_df["destination_id"]
    persons_df = persons_df[["person_id", "office_id", "origin_x", "origin_y",
                                "destination_x", "destination_y"]]
    persons_df.dropna(inplace=True)
    persons_df.to_csv(data_path+"/processed/persons.csv", sep=";", index=False)

def compute_offices_request(data_path, offices_file):
    persons = pd.read_csv(data_path+"/processed/persons.csv", sep=";")
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

    """
    df_commutes = df_commutes.rename(columns={
        "car_travel_time": "baseline_car_travel_time",
        "car_distance": "baseline_car_distance",
        "pt_travel_time": "baseline_pt_travel_time",
        "pt_distance": "baseline_pt_distance",
    })

    df_results = router.run(context, requests_df)

    return df
    """




if __name__ == "__main__":
    #from IPython import embed; embed()
    data_path = "/home/matt/git/tiers-lieux/data/"
    jar_file = "flow-1.2.0.jar"
    """
    compute_initial_requests(data_path)
    router.run(data_path, jar_file, "/processed/persons.csv",
                "/matsim-conf/toulouse_config.xml", "routed_initial.csv")
    compute_offices_request(data_path, "top50.txt")
    """
    router.run(data_path, jar_file, "/processed/offices_request.csv",
                "/matsim-conf/toulouse_config.xml", "routed_offices.csv")
