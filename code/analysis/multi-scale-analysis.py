#!/usr/bin/env python
# coding: utf-8

import sys, os
sys.path.append("/home/matt/git/tiers-lieux/code")
import utils
import geopandas as gpd
import pandas as pd
import router
import matplotlib as mpl
import numpy as np
import matplotlib.pyplot as plt
import yaml
import osmnx as ox

mpl.rcParams['figure.figsize'] = [15, 15]

conf_file = sys.argv[1]
with open(conf_file, "r") as yml_file:
        cfg = yaml.safe_load(yml_file)
data_path = os.path.abspath(cfg["data_path"])
processed_path = os.path.abspath(cfg["processed_path"])
departments = cfg["departments"]
iso = cfg["isochrone"]
presel_func = None
try:
    presel_func = cfg["preselection"]
except KeyError:
    pass

sub_territories = cfg["sub_territories"]
sub_processed_paths = []
sub_municipalities_lists = []
for territories_conf in sub_territories:
        with open(territories_conf, "r") as yml_file:
            sub_cfg = yaml.safe_load(yml_file)
        sub_municipalities_lists.append(utils.load_muni_list(sub_cfg))
        sub_processed_paths.append(sub_cfg["processed_path"])

r = router.Router(cfg)
saved_df_w = r.get_saved_distance(presel_func)
saved_df = saved_df_w.drop("weight", axis=1)
weight = saved_df_w["weight"]
nb_persons = weight.sum()

municipalities = gpd.read_file(f"{processed_path}/communes.gpkg")
municipalities_list = utils.load_muni_list(cfg)
if municipalities_list:
    municipalities = municipalities[municipalities["commune_id"].isin(municipalities_list)]

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

solver_res_path = f"{processed_path}/solver_res_iso{iso}.txt"
with open(solver_res_path) as f:
    l = f.readline()
    res = eval(l.strip())

#base map
cmap = mpl.cm.Blues(np.linspace(0,1,20))
cmap = mpl.colors.ListedColormap(cmap[5:,:-1])
m = municipalities[municipalities["density"]!=0]
#ax = m.plot(column="density", cmap=cmap, legend=True, scheme='user_defined', classification_kwds={'bins':[10,100,500,2000]})
ax = m.plot(column="density", cmap=cmap, legend=True, scheme="JenksCaspall", k=6, zorder=1)
ax.get_legend().set_title("Population")
departments.plot(ax=ax, facecolor='none', edgecolor='black', linewidth=1, zorder=2)
for sub_municipalities_list in sub_municipalities_lists:
    sub_municipalities = municipalities[municipalities["commune_id"].isin(sub_municipalities_list)]
    sub_municipalities.dissolve().plot(ax=ax, facecolor='none', edgecolor='black', linewidth=1, zorder=3)




#road network
path = f"{processed_path}/graph.graphml"
if os.path.exists(path):
    print("Loading road network")
    graph = ox.load_graphml(path)
else:
    print("Downloading road network")
    area = m.dissolve().to_crs(4326)
    cf = '["highway"~"motorway|trunk|primary|secondary"]'
    graph = ox.graph_from_polygon(area.geometry[0], network_type="drive", retain_all=True, truncate_by_edge=True, clean_periphery=True, custom_filter=cf)
    graph = ox.projection.project_graph(graph, to_crs=2154)
    ox.save_graphml(graph, filepath=path)
nodes, roads = ox.graph_to_gdfs(graph)
roads[roads.highway!="secondary"].plot(ax=ax, color="white", linewidth=1, alpha=0.4, zorder=3)
roads[roads.highway=="secondary"].plot(ax=ax, color="white", linewidth=0.5, alpha=0.4, zorder=4)

#municipalities
if presel_func:
    preselected_muni = municipalities[municipalities["commune_id"].isin(saved_df.columns
    )].copy()
    preselected_muni["geometry"] = preselected_muni.centroid
    preselected_muni.plot(ax=ax, color="orange", linewidth=3, zorder=10)
chosen_muni = municipalities[municipalities["commune_id"].isin(res[1])].copy()
chosen_muni["geometry"] = chosen_muni.centroid
chosen_muni.plot(ax=ax, color="red", linewidth=5, zorder=20)

for sub_processed_path in sub_processed_paths:
    solver_res_path = f"{sub_processed_path}/solver_res_iso{iso}.txt"
    with open(solver_res_path) as f:
        l = f.readline()
        res = eval(l.strip())
    chosen_muni = municipalities[municipalities["commune_id"].isin(res[1])].copy()
    chosen_muni["geometry"] = chosen_muni.centroid
    chosen_muni.plot(ax=ax, color="yellow", linewidth=1, zorder=20)

plt.axis('off')
plt.savefig(f"{processed_path}/multi-scale-map_iso{iso}.png", bbox_inches='tight')
