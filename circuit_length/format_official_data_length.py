import pandas as pd
import json

df = pd.read_csv("Health score coverage - Sheet1.csv", header=1)
df = df.fillna("")

print(df.columns)
kv_cols = {c.lower().split("kv")[0]:c for c in df.columns if "kv" in c.lower()}
print(kv_cols)

dictdata = {}
for row in df.to_dict(orient="records"):
    val = {}
    for lg_v, lg_f in kv_cols.items():
        if row[lg_f] != "":
            val[lg_v] = row[lg_f]
    if val:
        dictdata[row["ISO-2 Code"]] = val

js_data = "const data_voltage_length_official = " + str(dictdata) + ";"
with open("data_voltage_length_official.js", "w") as f:
    f.write(js_data)

import pprint
pprint.pp(dictdata)