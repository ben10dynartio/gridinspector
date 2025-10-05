import json
from pathlib import Path

import pandas as pd
import config

dfs = []
for ccode in config.WORLD_COUNTRY_DICT.keys():
    mypath = Path(Path(config.DATA_FOLDER_PATH) / ccode / f"{ccode}_quality_scores_grid_stats.json")
    if mypath.is_file():
        with open(mypath) as f:
            data = json.load(f)
        mydict = {r["key"]:r["value"] for r in data}
        mydf = pd.DataFrame([mydict])
        mydf.insert(0, "codeiso2", ccode)
        dfs.append(mydf)

df = pd.concat(dfs)
target_folder = Path(config.DATA_FOLDER_PATH) / "00_WORLD"
target_folder.mkdir(exist_ok=True)
df.to_csv(target_folder / "worldwide_quality_grid_stats.csv", index=False)