import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent / "common"))

import configapps

import geopandas as gpd
import ast
from pathlib import Path

import pandas as pd

lineres = []
subres = []

globcountry = ""

def to_int(row):
    try:
        if row["voltage"] is None:
            return -2
        else:
            lstv = row["voltage"].split(";")
            for v in lstv:
                int(v)
            return 1
    except Exception:
        print(f"Error in {globcountry} with voltage =", row["voltage"], f" | OSM line = https://openstreetmap.org/{row['osmid']}")
        return -1


for countrykey, countryname in configapps.WORLD_COUNTRY_DICT.items():
    #print("reading", countrykey, countryname)
    dfline = gpd.read_file((configapps.INPUT_GEODATA_FOLDER_PATH / countrykey) / "osm_brut_power_line.gpkg")
    dfsub = gpd.read_file((configapps.INPUT_GEODATA_FOLDER_PATH / countrykey) / "osm_brut_power_substation.gpkg")
    globcountry = f"{countryname} ({countrykey})"
    if len(dfline) == 0:
        #print("-- No line")
        pass
    else:
        dfline["tagsdict"] = dfline["tags"].apply(lambda x: ast.literal_eval(x))
        dfline["voltage"] = dfline["tagsdict"].apply(lambda x: x.get("voltage"))
        dfline["voltage_int"] = dfline.apply(lambda x:to_int(x), axis=1)
    if len(dfsub) == 0:
        pass
        #print("-- No sub")
    else:
        dfsub["tagsdict"] = dfsub["tags"].apply(lambda x: ast.literal_eval(x))
        dfsub["voltage"] = dfsub["tagsdict"].apply(lambda x: x.get("voltage"))
        dfsub["voltage_int"] = dfsub.apply(lambda x: to_int(x), axis=1)
