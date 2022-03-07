#!/usr/bin/env python
# coding: utf-8

# In[202]:


import matplotlib.pyplot as plt
import geopandas as gpd
import pandas as pd
import sys
import matplotlib as mpl

mpl.rcParams['figure.figsize'] = [20, 20]


# In[203]:


comminges = []
with open("comminges_insee.txt") as f:
    for c in f:
        comminges.append(c.strip())


# In[204]:


municipalities = gpd.read_file("../../data/iris/communes-20210101.shp")[["insee", "geometry"]]
municipalities.geometry = municipalities.geometry.to_crs(2154)
municipalities = municipalities.rename(columns={"insee": "commune_id"})
municipalities["commune_id"] = municipalities["commune_id"].astype(str)


# In[205]:


departments = ["09", "31", "32", "65"]
municipalities["department"] = municipalities["commune_id"].str[:2]
municipalities = municipalities[municipalities["department"].isin(departments)]
departments = municipalities.dissolve("department").reset_index()


# # Mob extern

# In[206]:


mob = pd.read_csv("../../data/base-flux-mobilite-domicile-lieu-travail-2018.csv", sep=";")
comminges_df = mob[mob.CODGEO.isin(comminges)& ~mob.DCLT.isin(comminges)]


comminges_df = comminges_df.merge(municipalities[["commune_id", "geometry"]],
                                    how='left',
                                    left_on='CODGEO',
                                    right_on='commune_id')
comminges_df.rename(columns={"geometry":"geometry_orig"}, inplace=True)

comminges_df = comminges_df.merge(municipalities[["commune_id", "geometry"]],
                                    how='left',
                                    left_on='DCLT',
                                    right_on='commune_id')
comminges_df.rename(columns={"geometry":"geometry_dest"}, inplace=True)
comminges_df.rename(columns={"geometry_orig":"geometry"}, inplace=True)
comminges_df = gpd.GeoDataFrame(comminges_df)
comminges_df["geometry_orig"] = comminges_df.geometry.centroid
comminges_df["geometry_dest"] = comminges_df.geometry_dest.centroid
comminges_df.dropna(inplace=True)


# In[208]:


cum_dest = comminges_df.groupby("DCLT", as_index=False).sum()
cum_dest.rename(columns={"NBFLUX_C18_ACTOCC15P":"cum_dest"}, inplace=True)
cum_dest = cum_dest.merge(municipalities, left_on="DCLT", right_on="commune_id", how="left")
cum_dest = gpd.GeoDataFrame(cum_dest)


# In[212]:


ax = municipalities.plot()
departments.plot(ax=ax, facecolor='none', edgecolor='black', linewidth=1)
gpd.GeoDataFrame(comminges_df).plot(ax=ax, color="green", edgecolor="black", linewidth=0.1)
df = comminges_df
for x_orig, x_dest, y_orig, y_dest, label_orig, label_dest, n in zip(
    df.geometry_orig.x, df.geometry_dest.x, df.geometry_orig.y, df.geometry_dest.y,
    df.LIBGEO, df.L_DCLT, df.NBFLUX_C18_ACTOCC15P):
        plt.plot([x_orig , x_dest], [y_orig, y_dest], linewidth=n/10, color="red", alpha=0.4)
        #plt.text(slon+0.5, slat+0.5, src_city, fontsize=8, color="dodgerblue", alpha=0.1, horizontalalignment='center', verticalalignment='center')
        if n > 16:
            plt.text(x_dest+0.5, y_dest+0.5, label_dest, fontsize=8, color="black", alpha=0.9, horizontalalignment='center', verticalalignment='center')
for x_dest, y_dest, n in zip(
    cum_dest.geometry.centroid.x, cum_dest.geometry.centroid.y, cum_dest.cum_dest):
    plt.scatter(x_dest, y_dest, color="yellow", s=n)
ax.set_axis_off()


# In[148]:


cum_dest = comminges_df.groupby("DCLT").sum()
cum_dest.rename(columns={"NBFLUX_C18_ACTOCC15P":"cum_dest"}, inplace=True)
comminges_df.merge(comminges_df.groupby("DCLT").sum(), on="DCLT")


# In[134]:


mob_comminges = gpd.GeoDataFrame(comminges_df.groupby("DCLT")["NBFLUX_C18_ACTOCC15P"].sum())
mob_comminges = mob_comminges.merge(municipalities[["commune_id", "geometry"]],
                                    how='left',
                                    left_on='DCLT',
                                    right_on='commune_id')
mob_comminges = mob_comminges.merge(comminges_df[["DCLT", "L_DCLT"]],
                                    how='left',
                                    left_on='commune_id',
                                    right_on='DCLT')
mob_comminges.geometry = mob_comminges.geometry.centroid
mob_comminges


# In[211]:


ax = municipalities.plot()
departments.plot(ax=ax, facecolor='none', edgecolor='black', linewidth=1)
gpd.GeoDataFrame(comminges_df).dissolve().plot(ax=ax, color="green")
center = gpd.GeoDataFrame(comminges_df).dissolve().centroid
df = mob_comminges

for x_dest, y_dest, label_dest, n in zip(
df.geometry.x, df.geometry.y, df.L_DCLT, df.NBFLUX_C18_ACTOCC15P):
        plt.plot([center.x , x_dest], [center.y, y_dest], linewidth=n/100, color="red", alpha=0.6)
        #plt.text(slon+0.5, slat+0.5, src_city, fontsize=8, color="dodgerblue", alpha=0.1, horizontalalignment='center', verticalalignment='center')
        if n > 40:
            plt.text(x_dest+0.5, y_dest+0.5, label_dest, fontsize=8, color="black", horizontalalignment='center', verticalalignment='center')
plt.scatter(center.x, center.y, color="yellow", alpha=1, s=100)
for x_dest, y_dest, n in zip(
    cum_dest.geometry.centroid.x, cum_dest.geometry.centroid.y, cum_dest.cum_dest):
    plt.scatter(x_dest, y_dest, color="yellow", s=n)
ax.set_axis_off()


# # Comminges intra

# In[214]:


comminges_df = mob[mob.CODGEO.isin(comminges)& mob.DCLT.isin(comminges)]


comminges_df = comminges_df.merge(municipalities[["commune_id", "geometry"]],
                                    how='left',
                                    left_on='CODGEO',
                                    right_on='commune_id')
comminges_df.rename(columns={"geometry":"geometry_orig"}, inplace=True)

comminges_df = comminges_df.merge(municipalities[["commune_id", "geometry"]],
                                    how='left',
                                    left_on='DCLT',
                                    right_on='commune_id')
comminges_df.rename(columns={"geometry":"geometry_dest"}, inplace=True)
comminges_df.rename(columns={"geometry_orig":"geometry"}, inplace=True)
comminges_df = gpd.GeoDataFrame(comminges_df)
comminges_df["geometry_orig"] = comminges_df.geometry.centroid
comminges_df["geometry_dest"] = comminges_df.geometry_dest.centroid
comminges_df.dropna(inplace=True)


# In[218]:


cum_dest = comminges_df.groupby("DCLT", as_index=False).sum()
cum_dest.rename(columns={"NBFLUX_C18_ACTOCC15P":"cum_dest"}, inplace=True)
cum_dest = cum_dest.merge(municipalities, left_on="DCLT", right_on="commune_id", how="left")
cum_dest = gpd.GeoDataFrame(cum_dest)
ax = gpd.GeoDataFrame(comminges_df).plot(color="green", edgecolor="black")
df = comminges_df
for x_orig, x_dest, y_orig, y_dest, label_orig, label_dest, n in zip(
    df.geometry_orig.x, df.geometry_dest.x, df.geometry_orig.y, df.geometry_dest.y,
    df.LIBGEO, df.L_DCLT, df.NBFLUX_C18_ACTOCC15P):
        plt.plot([x_orig , x_dest], [y_orig, y_dest], linewidth=n/10, color="red", alpha=0.4)
        #plt.text(slon+0.5, slat+0.5, src_city, fontsize=8, color="dodgerblue", alpha=0.1, horizontalalignment='center', verticalalignment='center')
        if n > 16:
            plt.text(x_dest+0.5, y_dest+0.5, label_dest, fontsize=8, color="black", alpha=1, horizontalalignment='center', verticalalignment='center')
for x_dest, y_dest, n in zip(
    cum_dest.geometry.centroid.x, cum_dest.geometry.centroid.y, cum_dest.cum_dest):
    plt.scatter(x_dest, y_dest, color="yellow", s=n)
ax.set_axis_off()


# In[ ]:




