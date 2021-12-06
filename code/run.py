import preprocessing.process_hr as hr
import preprocessing.communes as com
import pandas as pd
import numpy as np
import router


def compute_requests(data_path):
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


if __name__ == "__main__":
    #from IPython import embed; embed()
    data_path = "/home/matt/git/tiers-lieux/data/"
    jar_file = "flow-1.2.0.jar"
    compute_requests(data_path)
    router.run(data_path, jar_file, "/processed/persons.csv", "/matsim-conf/toulouse_config.xml")
