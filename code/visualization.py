import geopandas as gpd
import matplotlib.pyplot as plt
import pandas as pd

def viz(res):
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
    chosen_muni = municipalities[municipalities["commune_id"].isin(res[1])].copy()
    chosen_muni["geometry"] = chosen_muni.centroid
    #from IPython import embed; embed()
    persons_df = pd.read_csv("../data/processed/persons.csv")
    density_df = persons_df["origin_id"].value_counts()
    density_df = density_df.reset_index().rename(columns={"index":"commune_id",
                                                          "origin_id":"density"})
    municipalities = pd.merge(municipalities, density_df, on="commune_id",
                                how="left").fillna(0)
    municipalities.plot(column="density", cmap="Reds", scheme="quantiles")
    print(municipalities["geometry"])
    #gplt.choropleth(municipalities, hue='density', legend=True)
    plt.show()
    fig = departements.plot()
    chosen_muni.plot(ax=fig, color="red")
    plt.tight_layout()
    plt.show()
    #df.to_file("data/departments.gpkg", driver = "GPKG")

"""
res = (462489137.66859215,
 ['31555',
  '31160',
  '31364',
  '31424',
  '31582',
  '31087',
  '31473',
  '31079',
  '31374',
  '31395'])
viz(res)
"""
