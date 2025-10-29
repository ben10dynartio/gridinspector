import geopandas as gpd
import pandas as pd
from config import WORLD_COUNTRY_DICT

gdfs = []
for key in WORLD_COUNTRY_DICT.keys():
    filepath = "/home/ben/DevProjects/osm-power-grid-map-analysis/data/" + key + "/osm_brut_country_shape.gpkg"
    mygdf = gpd.read_file(filepath)
    mygdf["countrycode"] = key
    #print(key, mygdf)
    gdfs.append(mygdf)

gdf = gpd.GeoDataFrame(pd.concat(gdfs), geometry="geometry", crs=gdfs[0].crs)
gdf["geottype"] = gdf["geometry"].apply(lambda x: x.__class__.__name__)
gdf.to_file("data/worldmap_indicators.gpkg")

