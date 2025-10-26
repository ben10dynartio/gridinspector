import json
from pathlib import Path

import pandas as pd
import config

dfs = []
for ccode in config.WORLD_COUNTRY_DICT.keys():
    mypath : Path = Path(Path(config.DATA_FOLDER_PATH) / f"circuit_length/{ccode}_circuit_length.json")
    if mypath.is_file():
        with open(mypath) as f:
            data = json.load(f)
        if data is None:
            print("-- No circuit length for", ccode)
            continue
        mydict = {"codeiso2":ccode, "circuit_length_kv_km":data}
        mydf = pd.DataFrame([mydict])
        dfs.append(mydf)

df = pd.concat(dfs)
df.to_csv(config.OUTPUT_WORLDWIDE_FOLDER_PATH / "worldwide_circuit_length.csv", index=False)