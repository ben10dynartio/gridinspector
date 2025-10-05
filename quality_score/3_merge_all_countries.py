import json
from pathlib import Path

import pandas as pd
from config import WORLD_COUNTRY_DICT

dfs = []
for ccode in WORLD_COUNTRY_DICT.keys():
    mypath = Path(f"build/quality_score_{ccode}.json")
    if mypath.is_file():
        with open(mypath) as f:
            data = json.load(f)
        mydict = {r["key"]:r["value"] for r in data}
        mydf = pd.DataFrame([mydict])
        mydf["codeiso2"] = ccode
        dfs.append(mydf)

df = pd.concat(dfs)
df.to_excel("build/0_health_score.xlsx")