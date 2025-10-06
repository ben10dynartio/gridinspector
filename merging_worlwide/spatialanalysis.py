import json
from pathlib import Path

import pandas as pd
from config import WORLD_COUNTRY_DICT

dfs = []
for ccode in WORLD_COUNTRY_DICT.keys():
    mypath = Path(f"../build/{ccode}/stats_coverage.json")
    if mypath.is_file():
        with open(mypath) as f:
            mydict = json.load(f)
        mydict["codeiso2"] = ccode
        dfs.append(mydict)

df = pd.DataFrame(dfs)
df.to_excel("../build/0_coverage_score.xlsx")