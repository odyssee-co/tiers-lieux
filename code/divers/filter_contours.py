import geopandas as gpd


def filter_contours(iris_path, communes_path):
    """
    Filter coutours file for only the communes that we are interested in and
    store the result in pst_communes.gpkg
    """
    df = gpd.read_file(iris_path)
    with open(communes_path) as f:
        ids = [x.strip() for x in f]
    df = df[df["INSEE_COM"].isin(ids)]
    df = df[["INSEE_COM", "geometry"]].rename(
        columns={"INSEE_COM": "commune_id"})
    df = df.dissolve("commune_id")
    df.to_file("processed_data/pst_communes.gpkg", driver="GPKG")


iris_path = "data/iris_2017/CONTOURS-IRIS.shp"
communes_path = "data/insee_communes.txt"
filter_contours(iris_path, communes_path)
