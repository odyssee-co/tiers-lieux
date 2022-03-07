#!/usr/bin/env python
# coding: utf-8

# In[107]:


import sys
sys.path.append("..")
import geopandas as gpd
import pandas as pd
import router
import optimizer
import matplotlib as mpl
import geoplot as gplt
import numpy as np
import matplotlib.pyplot as plt 
mpl.rcParams['figure.figsize'] = [20, 20]


# In[108]:


df_names = pd.read_excel("../../data/reference_IRIS_geo2017.xls", skiprows = 5)
df_names["municipality_id"] = df_names["CODE_IRIS"].astype(str).str[:5]
df_names["label"] = df_names["LIBCOM"]
df_names = df_names[["municipality_id", "label"]]
df_names = df_names.drop_duplicates("municipality_id")


# In[109]:


processed_path = "../../data/processed/"
data_path = "../../data/"
departments = ["09", "11", "31", "32", "81", "82"]
matsim_conf = "matsim-conf/toulouse_config.xml"
exclude = ["31555"]
min_saved = 10
isochrone = 15
presel_func = None
suffix = f"_iso{isochrone}_min{min_saved}_{presel_func}"


population = pd.read_feather(f"{data_path}/processed/persons.feather")
r = router.Router(data_path, suffix, population, departments, matsim_conf, preselection=None)
saved_df_w = r.get_saved_distance(isochrone=isochrone, min_saved=min_saved, exclude=exclude)
saved_df = saved_df_w.drop("weight", axis=1)
weight = saved_df_w["weight"]
nb_persons = weight.sum()


# In[110]:


municipalities = gpd.read_file("../../data/municipalities.gpkg")[["commune_id", "geometry"]]
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
departments = departments[["label", "department", "geometry"]]


# In[111]:


persons_df = pd.read_feather("../../data/processed/persons.feather")
#persons_df = persons_df[persons_df["origin_id"].str[0:2].isin(["09", "82", "81", "11", "31", "32"])]

density_df = pd.DataFrame(persons_df.groupby("origin_id")["weight"].sum())
density_df = density_df.reset_index().rename(columns={"origin_id":"commune_id",
                                                      "weight":"density"})
municipalities = pd.merge(municipalities, density_df, on="commune_id",
                            how="left").fillna(0)
municipalities["density"] = municipalities["density"].astype(int)


# In[112]:


#res = optimizer.evolutionary(saved_df, 10, nb_it=300, verbose=True)


# In[113]:


#res = optimizer.mip(saved_df, 10, solver="cbc")
#res_46000 = (958271347.6296041, ["31087", "31098", "31160", "31364", "31374", "31395", "31424", "31555", "81271", "82121"])
res = (1985993614.156997, ['82121', '81004', '31395', '31149', '31113', '31561', '31187', '31118', '81271', '31248'])


# # Systemic analysis

# In[141]:


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
display(df[["label", "attractiveness", "saved_distance_km", "saved_distance_per_person_km"]].style.hide_index())


# # Visualization

# In[115]:


preselected_muni = municipalities[municipalities["commune_id"].isin(saved_df.columns
)].copy()
preselected_muni["geometry"] = preselected_muni.centroid
chosen_muni = municipalities[municipalities["commune_id"].isin(res[1])].copy()
chosen_muni["geometry"] = chosen_muni.centroid


# In[139]:


cmap = mpl.cm.Blues(np.linspace(0,1,20))
cmap = mpl.colors.ListedColormap(cmap[5:,:-1])
m = municipalities[municipalities["density"]!=0]
ax = m.plot(column="density", cmap=cmap, legend=True, scheme='user_defined', classification_kwds={'bins':[10,100,500,2000]})
#ax = m.plot(column="density", cmap=cmap, legend=True, scheme="JenksCaspall", k=6)

ax.get_legend().set_title("Population")
departments.plot(ax=ax, facecolor='none', edgecolor='black', linewidth=1)
#preselected_muni.plot(ax=ax, color="orange", linewidth=3)
chosen_muni.plot(ax=ax, color="red", linewidth=6)




# In[120]:


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


# In[41]:


results = [(608963335.8989906, [32425, 82121]),
(695732352.8472321, [31098, 31555, 82121]),
(754926346.7928385, [31087, 31098, 31555, 82121]),
(811535895.5562859, [31087, 31098, 31364, 31555, 82121]),
(851211150.2729416, [31087, 31098, 31364, 31395, 31555, 82121]),
(883909855.2464185, [31087, 31098, 31160, 31364, 31395, 31555, 82121]),
(915403852.6760631, [31087, 31098, 31160, 31364, 31374, 31395, 31555, 82121]),
(939494910.661215, [31087, 31098, 31160, 31364, 31374, 31395, 31424, 31555, 82121]),
(958271347.6296041, [31087, 31098, 31160, 31364, 31374, 31395, 31424, 31555, 81271, 82121]),
(973664401.0248519, [31087, 31098, 31160, 31297, 31364, 31374, 31395, 31424, 31555, 81271, 82121]),
(987743301.8523376, [31087, 31098, 31160, 31297, 31364, 31374, 31395, 31424, 31473, 31555, 81271, 82121]),
(1000955570.6752728, [31079, 31087, 31098, 31160, 31297, 31364, 31374, 31395, 31424, 31473, 31555, 81271, 82121]),
(1013023201.06589, [31079, 31087, 31098, 31160, 31291, 31297, 31364, 31374, 31395, 31424, 31473, 31555, 81271, 82121]),
(1022973084.9915361, [31079, 31087, 31098, 31160, 31203, 31291, 31297, 31364, 31374, 31395, 31424, 31473, 31555, 81271, 82121]),
(1031095645.0346969, [31079, 31087, 31098, 31160, 31203, 31248, 31291, 31297, 31364, 31374, 31395, 31424, 31473, 31555, 81271, 82121]),
(1038640454.5472208, [31079, 31087, 31098, 31160, 31184, 31203, 31248, 31291, 31297, 31364, 31374, 31395, 31424, 31473, 31555, 81271, 82121]),
(1046003323.9946077, [31079, 31087, 31098, 31160, 31184, 31203, 31248, 31261, 31291, 31297, 31364, 31374, 31395, 31424, 31473, 31555, 81271, 82121]),
(1052560728.9525453, [31079, 31087, 31098, 31160, 31184, 31203, 31248, 31261, 31291, 31297, 31364, 31374, 31395, 31424, 31473, 31555, 31561, 81271, 82121]),
(1057868157.5398768, [31079, 31087, 31098, 31160, 31184, 31203, 31248, 31261, 31291, 31297, 31364, 31374, 31395, 31424, 31473, 31480, 31555, 31561, 81271, 82121]),
(1063101078.189282, [31079, 31087, 31098, 31160, 31184, 31203, 31248, 31261, 31291, 31297, 31364, 31374, 31395, 31424, 31473, 31480, 31555, 31557, 31561, 81271, 82121]),
(1068263844.731067, [31079, 31087, 31091, 31098, 31160, 31184, 31203, 31248, 31261, 31291, 31297, 31364, 31374, 31395, 31424, 31473, 31480, 31555, 31557, 31561, 81271, 82121]),
(1073284270.3593634, [31079, 31087, 31091, 31098, 31160, 31184, 31203, 31248, 31261, 31291, 31297, 31364, 31374, 31395, 31424, 31473, 31480, 31555, 31557, 31561, 32425, 81271, 82121]),
(1077842302.6731393, [31079, 31087, 31091, 31098, 31160, 31184, 31203, 31248, 31261, 31291, 31297, 31364, 31374, 31395, 31424, 31442, 31473, 31480, 31555, 31557, 31561, 32425, 81271, 82121])
]


# In[42]:


saved_distance = []
for i in results:
    saved_distance.append(int(i[0]))
saved_distance = np.array(saved_distance)
saved_distance = saved_distance /1000000


# In[43]:


mpl.rcParams['figure.figsize'] = [8, 5.5]
plt.plot(range(2, len(saved_distance)+2),saved_distance)
plt.xlabel('Number of selected offices $n$')
plt.ylabel('Saved distance [1000 km]')
plt.grid()


# In[ ]:





# In[ ]:




