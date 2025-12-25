import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent / "common"))

import configapps

import json
from pathlib import Path

import pandas as pd

dfs = []
for ccode in configapps.WORLD_COUNTRY_DICT.keys():
    mypath : Path = Path(configapps.OUTPUT_FOLDER_PATH / "voltageoperator" / f"{ccode}_voltage_operator.json")
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
configapps.OUTPUT_WORLD_FOLDER_PATH.mkdir(exist_ok=True)
df.to_csv(configapps.OUTPUT_WORLD_FOLDER_PATH / "voltage_operator.csv", index=False)