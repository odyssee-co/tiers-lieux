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
mpl.rcParams['figure.figsize'] = [20, 20]

res_file = open(sys.argv[1], "r")
res = []
for l in res_file:
    res.append(eval(l.strip()))

with open("conf.yml", "r") as yml_file:
        cfg = yaml.safe_load(yml_file)
data_path = os.path.abspath(cfg["data_path"])
processed_path = os.path.abspath(cfg["processed_path"])
departments = cfg["departments"]

df_names = pd.read_excel(f"{data_path}/reference_IRIS_geo2017.xls", skiprows = 5)
df_names["municipality_id"] = df_names["CODE_IRIS"].astype(str).str[:5]
df_names["label"] = df_names["LIBCOM"]
df_names = df_names[["municipality_id", "label"]]
df_names = df_names.drop_duplicates("municipality_id")


r = router.Router(cfg)
saved_df_w = r.get_saved_distance("top_50_muni")
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

res_opti = (6885559056.596714, ['92012', '78646', '91174', '95018', '91377', '94046', '95127', '93051', '77288', '93029'])


optimal_muni = municipalities[municipalities["commune_id"].isin(res_opti[1])].copy()
optimal_muni["geometry"] = optimal_muni.centroid

"""
for r in res:
    id = round(r[0]/1e3)
    chosen_muni = municipalities[municipalities["commune_id"].isin(r[1])].copy()
    chosen_muni["geometry"] = chosen_muni.centroid
    cmap = mpl.cm.Blues(np.linspace(0,1,20))
    ax = departments.plot(facecolor='none', edgecolor='black', linewidth=1)
    chosen_muni.plot(ax=ax, color="blue", linewidth=6)
    optimal_muni.plot(ax=ax, color="red", linewidth=3)
    ax.set_axis_off()
    plt.title(id, fontsize=20)
    plt.savefig(f"{data_path}/visualization/{id}.png", bbox_inches='tight')
"""

optimal_muni = municipalities[municipalities["commune_id"].isin(res_opti[1])].copy()
optimal_muni["geometry"] = optimal_muni.centroid
ax = departments.plot(facecolor='none', edgecolor='black', linewidth=1)
optimal_muni.plot(ax=ax, color="red", linewidth=1)
n = len(res)
for r in res:
    id = round(r[0]/1e3)
    chosen_muni = municipalities[municipalities["commune_id"].isin(r[1])].copy()
    chosen_muni["geometry"] = chosen_muni.centroid
    chosen_muni.plot(ax=ax, color="blue", linewidth=1, alpha=1/n)
    ax.set_axis_off()
plt.show()
