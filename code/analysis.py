#!/usr/bin/env python
# coding: utf-8

import geopandas as gpd
import pandas as pd
import router
import optimizer
import matplotlib.cm
import matplotlib as plt
import numpy as np
plt.rcParams['figure.figsize'] = [20, 20]


# In[23]:


df_names = pd.read_excel("../data/reference_IRIS_geo2017.xls", skiprows = 5)
df_names["municipality_id"] = df_names["CODE_IRIS"].astype(str).str[:5]
df_names["label"] = df_names["LIBCOM"]
df_names = df_names[["municipality_id", "label"]]
df_names = df_names.drop_duplicates("municipality_id")
df_names



processed_path = "../data/processed"
r = router.Router("../data")
saved_df = r.get_saved_distance()



departments = ["09", "82", "81", "11", "31", "32"]

municipalities = gpd.read_file("../data/municipalities.gpkg")[["commune_id", "geometry"]]
municipalities["department"] = municipalities["commune_id"].str[:2]

municipalities = municipalities[municipalities["department"].isin(departments)]
departments = municipalities.dissolve("department").reset_index()
labels = {
        "09": "Ariège",
        "82": "Tarn-et-Garonne",
        "81": "Tarn",
        "11": "Aude",
        "31": "Haute-Garonne",
        "32": "Gers"
    }
departments["label"] = departments["department"].apply(lambda x: labels[x])
departements = departments[["label", "department", "geometry"]]



persons_df = pd.read_csv("../data/processed/persons.csv")
density_df = persons_df["origin_id"].value_counts()
density_df = density_df.reset_index().rename(columns={"index":"commune_id",
                                                      "origin_id":"density"})
municipalities = pd.merge(municipalities, density_df, on="commune_id",
                            how="left").fillna(0)



municipalities["density"] = municipalities["density"].astype(int)



#res = optimizer.evolutionary(saved_df, 10, verbose=True)
#res = optimizer.mip(saved_df, 10, solver="cbc")
res = (474406620.0448354, ['31079', '31087', '31160', '31184', '31248', '31395', '31424', '31473', '31555', '31582'])
#res = (555999978.4155363, ['31035', '31079', '31087', '31160', '31184', '31248', '31261', '31291', '31297', '31374', '31395', '31424', '31458', '31473', '31555', '31557', '31561', '32425', '81271', '82020'])


# # Systemic analysis


saved_df_res = saved_df[res[1]]
max_saved_per_person = pd.concat({"idxmax":saved_df_res.idxmax(axis=1), "max":saved_df_res.max(axis=1)}, axis=1)
municipalities_cum_saving = max_saved_per_person.groupby(["idxmax"])["max"].apply(sum)
municipalities_nb_chosen = max_saved_per_person.groupby(["idxmax"]).size()
df = pd.concat({"saved_distance_km":municipalities_cum_saving/1000, "nb_persons":municipalities_nb_chosen}, axis=1)
df.sort_values(by = "saved_distance_km", ascending = False)
df["saved_distance_per_person_km"] = df["saved_distance_km"]/df["nb_persons"]
df = df.reset_index()
df.rename(columns={"idxmax":"municipality_id"}, inplace=True)
df.merge(df_names, on="municipality_id", how="left")


# # Visualization


preselected_muni = municipalities[municipalities["commune_id"].isin(saved_df.columns
)].copy()
preselected_muni["geometry"] = preselected_muni.centroid
chosen_muni = municipalities[municipalities["commune_id"].isin(res[1])].copy()
chosen_muni["geometry"] = chosen_muni.centroid



cmap = plt.cm.Blues(np.linspace(0,1,20))
cmap = plt.colors.ListedColormap(cmap[5:,:-1])

m = municipalities[municipalities["density"]!=0]
ax = m.plot(column="density", cmap=cmap, legend=True, scheme='user_defined', classification_kwds={'bins':[10,100,1000]})
departements.plot(ax=ax, facecolor='none', edgecolor='black', linewidth=1)
preselected_muni.plot(ax=ax, color="orange", linewidth=3)
chosen_muni.plot(ax=ax, color="red", linewidth=3)
plt.pyplot.show()
