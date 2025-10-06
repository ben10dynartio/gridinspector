import json
from pathlib import Path

import pandas as pd
import config

dfs = []
for ccode in config.WORLD_COUNTRY_DICT.keys():
    mypath : Path = Path(config.DATA_FOLDER_PATH / "spatialanalysis" / f"{ccode}/{ccode}_spatial_coverage.json")
    if mypath.is_file():
        print("Open", mypath)
        with open(mypath) as f:
            mydict = json.load(f)
        dfs.append(mydict)

df = pd.DataFrame(dfs)
config.OUTPUT_WORLDWIDE_FOLDER_PATH.mkdir(exist_ok=True)
df.to_csv(config.OUTPUT_WORLDWIDE_FOLDER_PATH / "substation_spatial_coverage.csv", index=False)