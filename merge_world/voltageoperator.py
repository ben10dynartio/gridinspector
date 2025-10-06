import json
from pathlib import Path

import pandas as pd
import config

dfs = []
for ccode in config.WORLD_COUNTRY_DICT.keys():
    mypath : Path = Path(config.DATA_FOLDER_PATH / "voltageoperator" / f"{ccode}_voltage_operator.json")
    if mypath.is_file():
        with open(mypath) as f:
            mydict = json.load(f)
        for key in ["line_voltage", "line_operator", "line_operator_wikidata",
                    "substation_voltage", "substation_operator", "substation_operator_wikidata"]:
            if mydict[key]:
                mydict[key] = ";".join([str(v) for v in mydict[key] if v])
            else:
                mydict[key] = ""
        dfs.append(mydict)

df = pd.DataFrame(dfs)
config.OUTPUT_WORLDWIDE_FOLDER_PATH.mkdir(exist_ok=True)
df.to_csv(config.OUTPUT_WORLDWIDE_FOLDER_PATH / "voltage_operator.csv", index=False)