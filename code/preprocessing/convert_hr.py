import pandas as pd
import geopandas as gpd
import numpy as np
import tqdm

#path = "../../data/hr_origin_destination.csv"
#suffix = "_hr"

#path = "../../data/hr_origin_destination_with_airbus.csv"
#suffix = "_hr_with_airbus"

path = "../../data/airbus_origin_destination.csv"
suffix = "_airbus"

df = pd.read_csv(path, sep = ";", dtype = {
    "origin_id": str, "destination_id": str
})
df["person_id"] = np.arange(len(df))

df["employed"] = True
df["socioprofessional_class"] = "3"

df[["person_id", "employed", "socioprofessional_class", "file"]].to_csv(
    "../../data/persons%s.csv" % suffix, sep = ";"
)

df_zones = gpd.read_file("../../data/municipalities.gpkg")
df_zones["geometry"] = df_zones["geometry"].centroid
df_zones["commune_id"] = df_zones["commune_id"].astype(str)

df_home = df[["person_id", "origin_id", "file"]].rename(columns = {
    "origin_id": "commune_id"
})

df_home = pd.merge(df_zones, df_home, on = "commune_id")[[
    "person_id", "geometry", "commune_id", "file"
]]

df_home["purpose"] = "home"

df_work = df[["person_id", "destination_id", "file"]].rename(columns = {
    "destination_id": "commune_id"
})

df_work = pd.merge(df_zones, df_work, on = "commune_id")[[
    "person_id", "geometry", "commune_id", "file"
]]

df_work["purpose"] = "work"

df_activities = pd.concat([df_home, df_work])
df_activities["start_time"] = 0.0

if True:
    np.random.seed(0)

    f_home = df_activities["purpose"] == "home"
    commune_ids = set(df_activities.loc[f_home, "commune_id"].unique())

    df_addresses = gpd.read_file("../../data/bdtopo.gpkg")
    df_addresses["commune_id"] = df_addresses["commune_id"].astype(str)

    for commune_id in tqdm.tqdm(commune_ids):
        df_commune = df_addresses[df_addresses["commune_id"] == commune_id]

        if len(df_commune) > 0:
            f_commune = df_activities["commune_id"] == commune_id
            f_commune &= f_home

            indices = np.random.randint(len(df_commune), size = np.count_nonzero(f_commune))
            df_activities.loc[f_commune, "geometry"] = df_commune.iloc[indices]["geometry"].values

df_activities = df_activities[~df_activities["geometry"].isna()]
df_activities = df_activities[df_activities["person_id"].isin(
    df_activities[df_activities["purpose"] == "home"]["person_id"]
)]

df_activities[["person_id", "purpose", "start_time", "geometry", "file"]].to_file(
    "../../data/activities%s.gpkg" % suffix, driver = "GPKG"
)

print(np.count_nonzero(df_activities["purpose"] == "home"))
print(np.count_nonzero(df_activities["purpose"] == "work"))
