import json
from pathlib import Path

import pandas as pd
import config

print(" -- Aggregating Quality-Grid Stats")
dfs = []
no_qgstat_list = []
for ccode in config.WORLD_COUNTRY_DICT.keys():
    mypath : Path = Path(Path(config.DATA_FOLDER_PATH) / f"qgstats/{ccode}_quality_scores_grid_stats.json")
    if mypath.is_file():
        with open(mypath) as f:
            data = json.load(f)
        if data is None:
            no_qgstat_list.append(ccode)
            continue
        mydict = {r["key"]:r["value"] for r in data}
        mydf = pd.DataFrame([mydict])
        mydf.insert(0, "codeiso2", ccode)
        dfs.append(mydf)

print(" -- No qg stats for :", no_qgstat_list)
df = pd.concat(dfs)
df.to_csv(config.OUTPUT_WORLDWIDE_FOLDER_PATH / "worldwide_quality_grid_stats.csv", index=False)