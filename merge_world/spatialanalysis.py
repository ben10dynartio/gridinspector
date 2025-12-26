import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent / "common"))

import configapps

import json
from pathlib import Path

import pandas as pd

dfs = []
for ccode in configapps.WORLD_COUNTRY_DICT.keys():
    mypath : Path = Path(configapps.OUTPUT_FOLDER_PATH / "spatialanalysis" / f"{ccode}/{ccode}_spatial_coverage.json")
    if mypath.is_file():
        #print("Open", mypath)
        with open(mypath) as f:
            mydict = json.load(f)
        dfs.append(mydict)

df = pd.DataFrame(dfs)
configapps.OUTPUT_WORLD_FOLDER_PATH.mkdir(exist_ok=True)
df.to_csv(configapps.OUTPUT_WORLD_FOLDER_PATH / "substation_spatial_coverage.csv", index=False)