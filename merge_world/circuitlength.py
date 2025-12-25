import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent / "common"))

import configapps
from utils_data import convert_int

import json

import pandas as pd


dfs = []
for ccode in configapps.WORLD_COUNTRY_DICT.keys():
    mypath : Path = Path(Path(configapps.OUTPUT_FOLDER_PATH) / f"circuit_length/{ccode}_circuit_length.json")
    if mypath.is_file():
        with open(mypath) as f:
            data = json.load(f)
        if data is None:
            print("-- No circuit length for", ccode)
            continue
        mydict = {"codeiso2":ccode, **data}
        mydf = pd.DataFrame([mydict])
        dfs.append(mydf)

df = pd.concat(dfs)
df["osm_way_above_50kv_length_km"] = df["osm_way_above_50kv_length_km"].apply(lambda x: convert_int(x, default=None, error=None))
df["osm_circuit_above_50kv_length_km"] = df["osm_circuit_above_50kv_length_km"].apply(lambda x: convert_int(x, default=None, error=None))
df.to_csv(configapps.OUTPUT_WORLD_FOLDER_PATH / "worldwide_circuit_length.csv", index=False)