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
import dataframe_image as dfi
import osmnx as ox
import optimizer
from itertools import product
from matplotlib_scalebar.scalebar import ScaleBar

mpl.rcParams['figure.figsize'] = [15, 15]

yml_path = sys.argv[1]
data_path, processed_path, orig_dep, dest_dep, departments, muni_orig,\
pop_src, exclude, matsim_conf, presel_functions,optimizations, nb_offices,\
isochrones, minimals = utils.parse_cfg(yml_path)

df_names = pd.read_excel(f"{data_path}/reference_IRIS_geo2017.xls", skiprows = 5)
df_names["municipality_id"] = df_names["CODE_IRIS"].astype(str).str[:5]
df_names["label"] = df_names["LIBCOM"]
df_names = df_names[["municipality_id", "label"]]
df_names = df_names.drop_duplicates("municipality_id")

router = router.Router(data_path, processed_path, exclude, matsim_conf)


municipalities = gpd.read_file(f"{processed_path}/communes.gpkg")
if muni_orig:
    municipalities = municipalities[municipalities["commune_id"].isin(muni_orig)]

elif orig_dep:
    municipalities = municipalities[municipalities["commune_id"].str[:2].isin(orig_dep)]
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
m = municipalities[municipalities["density"]!=0]

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

r = pd.read_csv(f"{processed_path}/res.csv", sep=";")

"""
#base map
cmap = mpl.cm.Blues(np.linspace(0,1,20))
cmap = mpl.colors.ListedColormap(cmap[5:,:-1])
#ax = m.plot(column="density", cmap=cmap, legend=True, scheme='user_defined', classification_kwds={'bins':[10,100,500,2000]})
ax = m.plot(column="density", cmap=cmap, legend=True, scheme="JenksCaspall", k=6, zorder=1)
ax.get_legend().set_title("Population")
departments.plot(ax=ax, facecolor='none', edgecolor='black', linewidth=1, zorder=5)
ax.set_axis_off()
#road network
roads[roads.highway!="secondary"].plot(ax=ax, color="white", linewidth=1, alpha=0.4, zorder=3)
roads[roads.highway=="secondary"].plot(ax=ax, color="white", linewidth=0.5, alpha=0.4, zorder=4)
pref  = ["Foix", "Montauban", "Albi", "Carcassonne", "Toulouse", "Auch"]
for i, p in m[m.nom.isin(pref)].iterrows():
    plt.text(p.x+0.5, p.y+0.5, p.nom, fontsize=10, color="black", alpha=1,
    horizontalalignment='center', verticalalignment='center', zorder=6,
    bbox=dict(facecolor='white', edgecolor='black', boxstyle='round,pad=0.3', alpha=0.8))
ax.add_artist(ScaleBar(1, location="lower right"))
plt.savefig(f"{processed_path}/basemap.png", bbox_inches='tight')
"""


for iso, min, presel, opt, n in product(isochrones, minimals, presel_functions, optimizations, nb_offices):
    suffix = f"_n{n}_iso{iso}_min{min}_{opt}_{presel}"
    saved_df_w = router.get_saved_distance(iso, min, presel)
    saved_df = saved_df_w.drop("weight", axis=1)
    weight = saved_df_w["weight"]
    nb_persons = weight.sum()

    sel = r[(r.n==n)&(r.iso==iso)&(r["min"]==min)&(r.presel==presel)&(r.optimizer==opt)].iloc[0]
    res = (sel.saved_d, eval(sel.selected_muni))

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
    df["saved_distance_km"] *= 2 #to take in account the return traject
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
    print(df[["label", "attractiveness", "saved_distance_km",
                "saved_distance_per_person_km"]].to_string(index=False))
    dfi.export(df[["label", "attractiveness", "saved_distance_km", "saved_distance_per_person_km"]], f"{processed_path}/tab{suffix}.png")
    #dfi.export(df[:-1][["label", "attractiveness", "saved_distance_per_person_km"]], f"{processed_path}/tab{suffix}.png")


    #base map
    cmap = mpl.cm.Blues(np.linspace(0,1,20))
    cmap = mpl.colors.ListedColormap(cmap[5:,:-1])
    #ax = m.plot(column="density", cmap=cmap, legend=True, scheme='user_defined', classification_kwds={'bins':[10,100,500,2000]})
    ax = m.plot(column="density", cmap=cmap, legend=True, scheme="JenksCaspall", k=6, zorder=1)
    ax.get_legend().set_title("Population")
    ax.add_artist(ScaleBar(1, location="lower right"))
    departments.plot(ax=ax, facecolor='none', edgecolor='black', linewidth=1, zorder=2)
    ax.set_axis_off()
    #road network
    roads[roads.highway!="secondary"].plot(ax=ax, color="white", linewidth=1, alpha=0.2, zorder=3)
    roads[roads.highway=="secondary"].plot(ax=ax, color="white", linewidth=0.5, alpha=0.2, zorder=4)
    #municipalities
    if presel != "all":
        #saved_df_presel_w = router.get_saved_distance(presel_func)
        #saved_df_presel = saved_df_presel_w.drop("weight", axis=1)
        preselected_muni = municipalities[municipalities["commune_id"].isin(saved_df.columns
        )].copy()
        preselected_muni["geometry"] = preselected_muni.centroid
        #preselected_muni.plot(ax=ax, color="orange", linewidth=3, zorder=10)
    chosen_muni = municipalities[municipalities["commune_id"].isin(res[1])].copy()
    chosen_muni["geometry"] = chosen_muni.centroid
    chosen_muni.plot(ax=ax, color="red", linewidth=5, zorder=20)
    for i, row in chosen_muni.iterrows():
        g = row.geometry
        plt.text(g.x+0.5, g.y+2000, row.nom, fontsize=10, color="black", alpha=1,
        horizontalalignment='center', verticalalignment='center', zorder=6,
        bbox=dict(facecolor='white', edgecolor='black', boxstyle='round,pad=0.3', alpha=0.8))
    plt.axis('off')
    plt.savefig(f"{processed_path}/map{suffix}.png", bbox_inches='tight')

    #multiple runs
    path_res_100 = f"{processed_path}/res_100.txt"
    if os.path.exists(path_res_100):
        res_file = open(path_res_100, "r")
        res_100 = []
        for l in res_file:
            res_100.append(eval(l.strip()))

        ax = departments.plot(facecolor='none', edgecolor='black', linewidth=1.5)
        roads[roads.highway!="secondary"].plot(ax=ax, color="black", linewidth=0.5, alpha=0.4, zorder=3)
        #roads[roads.highway=="secondary"].plot(ax=ax, color="black", linewidth=0.5, alpha=0.4, zorder=4)
        #chosen_muni.plot(ax=ax, color="red", linewidth=5)
        n = len(res_100)
        for r in res_100:
            muni = municipalities[municipalities["commune_id"].isin(r[1])].copy()
            muni["geometry"] = muni.centroid
            muni.plot(ax=ax, color="blue", linewidth=3, alpha=2/n)
            ax.set_axis_off()
        plt.savefig(f"{processed_path}/multiple_map.png", bbox_inches='tight')

        #most occurence in multiple runs
        d = {}
        for r in res_100:
            for muni in r[1]:
                if muni in d:
                    d[muni] += 1
                else:
                    d[muni] = 0
        s = pd.Series(d, name="count")
        s.index.name="commune_id"
        top_50 = list(s.sort_values(ascending=False)[:50].index)
        top_10 = list(s.sort_values(ascending=False)[:10].index)

        ax = departments.plot(facecolor='none', edgecolor='black', linewidth=1.5)
        roads[roads.highway!="secondary"].plot(ax=ax, color="black", linewidth=0.5, alpha=0.4, zorder=3)
        #roads[roads.highway=="secondary"].plot(ax=ax, color="black", linewidth=0.5, alpha=0.4, zorder=4)
        chosen_muni.plot(ax=ax, color="red", linewidth=5)

        top_50_df = municipalities[municipalities["commune_id"].isin(top_50)].copy()
        top_50_df["geometry"] = top_50_df.centroid
        top_50_df.plot(ax=ax, color="blue", linewidth=3, alpha=0.5, zorder=20)
        ax.set_axis_off()
        plt.savefig(f"{processed_path}/top_50_map.png", bbox_inches='tight')

        print(f"opti: {optimizer.eval(saved_df[res[1]])}")
        print(f"top_10: {optimizer.eval(saved_df[top_10])}")

    #hérisson
    df = persons_df.join(saved_df_res.idxmax(axis=1).rename("cw_id"))
    df = df[saved_df_res.max(axis=1)>0]
    df = df[df["origin_id"]!=df["cw_id"]]
    df = df.merge(municipalities[["commune_id","geometry"]], left_on="origin_id", right_on="commune_id", how="left")
    df.rename(columns={"geometry":"geometry_orig"}, inplace = True)
    df = df.merge(municipalities[["commune_id","geometry"]], left_on="cw_id", right_on="commune_id", how="left")
    df.rename(columns={"geometry":"geometry_dest"}, inplace = True)
    df = gpd.GeoDataFrame(df)
    df["geometry_orig"] = df.geometry_orig.centroid
    df["geometry_dest"] = df.geometry_dest.centroid
    ax = departments.plot(facecolor='none', edgecolor='black', linewidth=1, zorder=2)
    roads[roads.highway!="secondary"].plot(ax=ax, color="black", linewidth=1, alpha=0.2, zorder=3)
    roads[roads.highway=="secondary"].plot(ax=ax, color="black", linewidth=0.5, alpha=0.2, zorder=4)
    ax.set_axis_off()
    max_n = df.weight.max()
    print(df.weight.sum())
    for x_orig, x_dest, y_orig, y_dest, n in zip(
        df.geometry_orig.x, df.geometry_dest.x, df.geometry_orig.y, df.geometry_dest.y,
        df.weight):
            ax.plot([x_orig , x_dest], [y_orig, y_dest], color="blue", linewidth=0.1+3*n/max_n, alpha=1)
    ax.set_axis_off()
    plt.savefig(f"{processed_path}/herisson{suffix}.png", bbox_inches='tight')

print(f"nb_persons = {nb_persons}")
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
