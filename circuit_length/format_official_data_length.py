import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent / "common"))

import configapps

import pandas as pd
import json
from pathlib import Path
import re

print("> Formatting official circuit length data")
df : pd.DataFrame = pd.read_csv(Path(__file__).parent / "Grid Length coverage - Official Grid Lengths.csv", header=1)
df = df.fillna("")

range_columns = [c for c in df.columns if re.match(r'^\d{2,3}kv-\d{2,3}kv$', c.lower().replace(" ",""))]
value_columns = [c for c in df.columns if re.match(r'^\d{2,3}kv[^-]*$', c.lower().replace(" ",""))]

dictdata = {}

for row in df.to_dict(orient="records"):
    dictdata[row['ISO-2 Code']] = {"ranges":[], "values":[]}

    for col in range_columns:
        myrangedict = {}
        try:
            myval = int(row[col])
            rgsplit = col.lower().replace(" ", "").replace("kv", "").split("-")
            myrangedict["lowv"] = int(rgsplit[0])
            myrangedict["highv"] = int(rgsplit[1])
            myrangedict["km"] = myval
            dictdata[row['ISO-2 Code']]["ranges"].append(myrangedict)
        except Exception:
            pass

    for col in value_columns:
        myrangedict = {}
        try:
            myval = int(row[col])
            rgsplit = col.lower().replace(" ", "").split("kv")
            myrangedict["kv"] = int(rgsplit[0])
            myrangedict["km"] = myval
            dictdata[row['ISO-2 Code']]["values"].append(myrangedict)
        except Exception:
            pass

    try:
        myval = int(row["Total"])
        dictdata[row['ISO-2 Code']]["total"] = myval
    except Exception:
        pass


print("RESULTATS")
import pprint
pprint.pp(dictdata)

export_json_file = configapps.OUTPUT_FOLDER_PATH / "00_WORLD/data_circuit_length_official.json"
with open(export_json_file, "w") as f:
    json.dump(dictdata, f)
