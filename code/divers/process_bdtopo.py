import fiona
import pandas as pd
import shapely.geometry as geo
import geopandas as gpd
from tqdm import tqdm


def process_bdtopo(shape_file, departments):
    """
    Scan ADDRESSE.shp, filter by departments, extract CODE_INSEE and coordinates
    and write the result in a gpkg file
    """
    df = []
    with fiona.open(shape_file) as archive:
        pbar = tqdm(archive)
        for item in pbar:
            code = item["properties"]["CODE_INSEE"]
            if code[:2] in departments or code[:3] in departments:
                df.append(dict(
                    geometry=geo.Point(*item["geometry"]["coordinates"]),
                    commune_id=item["properties"]["CODE_INSEE"]
                ))

    df = pd.DataFrame.from_records(df)
    df = gpd.GeoDataFrame(df, crs="EPSG:2154")
    df.to_file("processed_data/bdtopo.gpkg", driver="GPKG")


departments = ["09", "82", "81", "11", "31", "32"]
shape_file = "data/bdtopo/ADRESSE.shp"
process_bdtopo(shape_file, departments)
