#!/usr/bin/env python
# coding: utf-8

import sys, os
sys.path.append("/home/matt/git/tiers-lieux/code")
import geopandas as gpd
import pandas as pd
import router
import matplotlib as mpl
import numpy as np
import matplotlib.pyplot as plt
import yaml
import dataframe_image as dfi

mpl.rcParams['figure.figsize'] = [15, 15]

with open("../data/conf-toulouse.yml", "r") as yml_file:
        cfg = yaml.safe_load(yml_file)
data_path = os.path.abspath(cfg["data_path"])
processed_path = os.path.abspath(cfg["processed_path"])
departments = cfg["departments"]
iso = cfg["isochrone"]

df_names = pd.read_excel(f"{data_path}/reference_IRIS_geo2017.xls", skiprows = 5)
df_names["municipality_id"] = df_names["CODE_IRIS"].astype(str).str[:5]
df_names["label"] = df_names["LIBCOM"]
df_names = df_names[["municipality_id", "label"]]
df_names = df_names.drop_duplicates("municipality_id")


r = router.Router(cfg)
saved_df_w = r.get_saved_distance("top_50")
saved_df = saved_df_w.drop("weight", axis=1)
weight = saved_df_w["weight"]
nb_persons = weight.sum()


municipalities = gpd.read_file(f"{processed_path}/communes.gpkg")
municipalities["department"] = municipalities["commune_id"].str[:2]
departments = municipalities.dissolve("department").reset_index()
dep_name = pd.read_csv(f"{data_path}/departements-france.csv")
departments = departments.merge(dep_name, left_on="department", right_on="code_departement", how="left")
departments.rename(columns={"nom_departement":"label"}, inplace=True)
departments = departments[["label", "department", "geometry"]]


persons_df = pd.read_feather(f"{processed_path}/persons.feather")
density_df = pd.DataFrame(persons_df.groupby("origin_id")["weight"].sum())
density_df = density_df.reset_index().rename(columns={"origin_id":"commune_id",
                                                      "weight":"density"})
municipalities = pd.merge(municipalities, density_df, on="commune_id",
                            how="left").fillna(0)
municipalities["density"] = municipalities["density"].astype(int)

if iso==15:
    res = (1985993614.156997, ['82121', '81004', '31395', '31149', '31113', '31561', '31187', '31118', '81271', '31248'])
if iso==30:
    res = (2813509837.849502, ['82121', '81004', '81065', '31395', '31561', '31187', '31118', '32160', '81271', '31248'])
if iso==60:
    res = (3082042712.2676554, ['82121', '81004', '31395', '31561', '31187', '31118', '11076', '32160', '81271', '31248'])

saved_df_res = saved_df[res[1]].copy()
max_saved_per_person = pd.concat({"idxmax":saved_df_res.idxmax(axis=1), "max":saved_df_res.max(axis=1)}, axis=1)
max_saved_per_person = max_saved_per_person[max_saved_per_person["max"]>0]
municipalities_cum_saving = pd.DataFrame(max_saved_per_person.
                                         groupby(["idxmax"])["max"].apply(sum))
municipalities_nb_chosen = max_saved_per_person.groupby(["idxmax"]).size()
municipalities_nb_chosen = max_saved_per_person.merge(pd.DataFrame(weight),
                                                      on="person_id", how="left")
municipalities_nb_chosen = pd.DataFrame(municipalities_nb_chosen.
                                        groupby("idxmax")["weight"].sum())

df = municipalities_cum_saving.merge(municipalities_nb_chosen, on="idxmax")
df.rename(columns={"max":"saved_distance_km", "weight":"attractiveness"}, inplace=True)
df["saved_distance_km"] /= 1000
df = df.sort_values(by = "saved_distance_km", ascending = False)
df["saved_distance_per_person_km"] = df["saved_distance_km"]/df["attractiveness"]
df = df.reset_index()
df.rename(columns={"idxmax":"municipality_id"}, inplace=True)
df = df.merge(df_names, on="municipality_id", how="left")

pd.set_option("precision", 2)
total = dict(df.sum(numeric_only=True))
total["label"] = "TOTAL"
total["saved_distance_per_person_km"] = total["saved_distance_km"]/nb_persons
df = df.append(total, ignore_index=True)
df["attractiveness"] = df["attractiveness"].astype(int)
df["saved_distance_km"] = df["saved_distance_km"].astype(int)
dfi.export(df[["label", "attractiveness", "saved_distance_km",
            "saved_distance_per_person_km"]], f"{processed_path}/tab-iso{iso}.png")


preselected_muni = municipalities[municipalities["commune_id"].isin(saved_df.columns
)].copy()
preselected_muni["geometry"] = preselected_muni.centroid
chosen_muni = municipalities[municipalities["commune_id"].isin(res[1])].copy()
chosen_muni["geometry"] = chosen_muni.centroid


cmap = mpl.cm.Blues(np.linspace(0,1,20))
cmap = mpl.colors.ListedColormap(cmap[5:,:-1])
m = municipalities[municipalities["density"]!=0]
#ax = m.plot(column="density", cmap=cmap, legend=True, scheme='user_defined', classification_kwds={'bins':[10,100,500,2000]})
ax = m.plot(column="density", cmap=cmap, legend=True, scheme="JenksCaspall", k=6)
ax.get_legend().set_title("Population")
departments.plot(ax=ax, facecolor='none', edgecolor='black', linewidth=1)
preselected_muni.plot(ax=ax, color="orange", linewidth=3)
chosen_muni.plot(ax=ax, color="red", linewidth=5)
plt.axis('off')
plt.savefig(f"{processed_path}/map_iso{iso}.png", bbox_inches='tight')

"""
# Plot labels
old = ["31555", "31467", "31424", "31107", "82121", "31395", "31451", "31033", "81004", "81271", "32160"]
old_chosen_muni = municipalities[municipalities["commune_id"].isin(old)].copy()
old_chosen_muni["geometry"] = old_chosen_muni.centroid
ax = departments.plot(facecolor='none', edgecolor='black', linewidth=1)
chosen_muni.plot(ax=ax, color="red", linewidth=12)
old_chosen_muni.plot(ax=ax, color="blue", linewidth=4)
all_muni = pd.merge(chosen_muni, old_chosen_muni, on=["commune_id", "geometry"], how="outer")
all_muni = pd.merge(all_muni, df_names.rename(columns={"municipality_id":"commune_id"}), on="commune_id", how="left")
for x, y, label in zip(all_muni.geometry.x, all_muni.geometry.y, all_muni.label):
    ax.annotate(label, xy=(x, y), xytext=(3, 3), textcoords="offset points")


# Plot saved distance in function of nb offices

saved_distance = []
for i in results:
    saved_distance.append(int(i[0]))
saved_distance = np.array(saved_distance)
saved_distance = saved_distance /1000000
mpl.rcParams['figure.figsize'] = [8, 5.5]
plt.plot(range(2, len(saved_distance)+2),saved_distance)
plt.xlabel('Number of selected offices $n$')
plt.ylabel('Saved distance [1000 km]')
plt.grid()
"""
