import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent / "common"))

import configapps

import json
import ast


import pandas as pd

def clamp(n, smallest, largest):
    return max(smallest, min(n, largest))

def symetric1(numerator, denominator):
    """ numerator & denominator both >0"""
    if denominator == 0:
        return 0
    v = numerator/denominator
    if v > 1:
        v = 2 - v
    return clamp(v, 0, 1)

print("> Worldwide voltage comparison")

export_json_file = configapps.OUTPUT_WORLD_FOLDER_PATH / "data_circuit_length_official.json"
with open(export_json_file, 'r') as f:
    official_data = json.load(f)

export_osm_file = configapps.OUTPUT_WORLD_FOLDER_PATH / f"worldwide_circuit_length.csv"
df = pd.read_csv(export_osm_file).set_index("codeiso2")



result = []
for countrykey, cdata in official_data.items():
    if countrykey not in df.index:
        continue
    osmvoltdict = ast.literal_eval(df.loc[countrykey]["circuit_length_kv_km"])
    osmvoltdict_float = {float(key):val for key, val in osmvoltdict.items()}
    #result.append("codeiso2":countrykey, "votage":160, "osm_km")

    mycompvalues = []
    myvoltvalues = []
    sum_off_kvkm = 0
    sum_osm_kvkm = 0

    sum_kv = 0
    sum_quality = 0

    for rg in cdata["ranges"]:
        #print("----------", rg)
        osmvalue = round(sum([km for kv, km in osmvoltdict_float.items() if (kv >= rg["lowv"]) and (kv >= rg["highv"])]))
        offvalue = rg["km"]
        text = f"{rg['lowv']}-{rg['highv']}"
        mycompvalues.append(f"{text}:{offvalue}:{osmvalue}")
        # Compute quality Score
        myvolt = (rg['lowv']+rg['highv'])/2
        myvoltvalues.append(myvolt)
        sum_kv += myvolt * offvalue
        sum_quality += symetric1(osmvalue, offvalue) * myvolt * offvalue

    for rg in cdata["values"]:
        osmvalue = round(float(osmvoltdict.get(str(rg["kv"]), 0)))
        offvalue = rg["km"]
        text = f"{rg['kv']}"
        mycompvalues.append(f"{text}:{offvalue}:{osmvalue}")
        # Compute quality Score
        myvolt = rg['kv']
        myvoltvalues.append(myvolt)
        sum_kv += myvolt * offvalue
        sum_quality += symetric1(osmvalue, offvalue) * myvolt * offvalue

    if mycompvalues == []: # if no other data, transmission voltage is considered above 50 kV
        osmvalue = round(sum([km for kv, km in osmvoltdict_float.items() if kv >= 50]))
        offvalue = cdata.get("total", 0)
        if offvalue > 0:
            text = f"Total"
            myvoltvalues.append(myvolt)
            mycompvalues.append(f"{text}:{offvalue}:{osmvalue}")
            # Compute quality Score
            coverage = symetric1(osmvalue, offvalue) * 100
        else:
            coverage = 0
    else:
        coverage = (sum_quality / sum_kv) * 100
    coverage = round(coverage, 1)

    # Associer index et values, trier, puis séparer
    myvoltvalues, mycompvalues = zip(*sorted(zip(myvoltvalues, mycompvalues)))
    mycompvalues = list(mycompvalues)

    result.append({"codeiso2":countrykey, "comparison_km_circuit_kv_off_osm":" ".join(mycompvalues), "comparison_coverage_score":coverage})

df = pd.DataFrame(result)
df.to_csv(configapps.OUTPUT_WORLD_FOLDER_PATH / "comparison_circuit_length_official_osm.csv", index=False)