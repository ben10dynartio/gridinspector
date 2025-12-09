import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent / "common"))

import configapps

import json

import pandas as pd


dfs = []
for ccode in configapps.WORLD_COUNTRY_DICT.keys():
    mypath : Path = Path(Path(configapps.DATA_FOLDER_PATH) / f"circuit_length/{ccode}_circuit_length.json")
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
df.to_csv(configapps.OUTPUT_WORLD_FOLDER_PATH / "worldwide_circuit_length.csv", index=False)