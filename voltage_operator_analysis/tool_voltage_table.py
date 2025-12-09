import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent / "common"))

import configapps

import pandas as pd
import bokeh
import ast

dfl = pd.read_excel("osm_country_data_power_line.xlsx", na_filter=False)
dfc = pd.read_csv("wikidata_countries_info_brut.csv", na_filter=False)

dictflag = {r["codeiso2"]:r["flag_image"] for r in dfc.to_dict(orient='records')}
dictname = {r["codeiso2"]:r["countryLabel"] for r in dfc.to_dict(orient='records')}

print(dfl.columns)
print(dfc.columns)
df = dfl.merge(dfc, left_on="Country Code", right_on="codeiso2", how='left')

df["Line voltage"] = df["Line voltage"].apply(lambda x: ast.literal_eval(x))
lstvoltage = df["Line voltage"].tolist()
lstvoltage = list(set(sum(lstvoltage, [])))
lstvoltage = [v for v in lstvoltage if v >= 50000]
lstvoltage.sort()


voltdict = {}
htmlreturn = "<table>"
for voltage in lstvoltage:
    temp = df[df["Line voltage"].apply(lambda x: voltage in x)]
    voltdict[voltage] = list(temp["codeiso2"])
    print("Voltage", voltage, "in =", voltdict[voltage])
    htmlreturn += f"\n<tr><td><b>{voltage}</b></td>"
    for myc in voltdict[voltage]:
        myurl = f'https://overpass-turbo.eu/?R&Q=%5Bout%3Ajson%5D%5Btimeout%3A180%5D%3B%0Aarea%5B%22ISO3166-1%22%3D%22{myc}%22%5D%5Badmin_level%3D2%5D-%3E.searchArea%3B%0A%0A%28%0A%20%20way%5B%22power%22%3D%22line%22%5D%5B%22voltage%22~%22%28%5E%7C%3B%29{voltage}%28%3B%7C%24%29%22%5D%28area.searchArea%29%3B%0A%20%20relation%5B%22power%22%3D%22line%22%5D%5B%22voltage%22~%22%28%5E%7C%3B%29{voltage}%28%3B%7C%24%29%22%5D%28area.searchArea%29%3B%0A%29%3B%0A%0Aout%20body%3B%0A%3E%3B%0Aout%20skel%20qt%3B'
        htmlreturn += f"<td><a href='{myurl}' target='_blank'><img src='{dictflag[myc]}' width='20' alt='{dictname[myc]}'></a></td>"
    htmlreturn += "</tr>"
htmlreturn += "</table>"

max_nb_country = max([len(val) for val in voltdict.values()])

myurl = 'https://overpass-turbo.eu/?Q=[out:json][timeout:180];%0A{{geocodeArea:FR}}->.searchArea;%0A(%0Away["power"~"^line|minor_line$"]["voltage"~"(^|;)20000(;|$)"](area.searchArea);%0Arelation["power"~"^line|minor_line$"]["voltage"~"(^|;)20000(;|$)"](area.searchArea);%0A);%0Aout%20body;%0A>;%0Aout%20skel%20qt;&R'

myurl = 'https://overpass-turbo.eu/?Q=[out:json][timeout:180];%0A{{geocodeArea:SE}}->.searchArea;%0A(%0Away["power=line"]["voltage"~"(^|;)412000(;|$)"](area.searchArea);%0Arelation["power=line"]["voltage"~"(^|;)412000(;|$)"](area.searchArea);%0A);%0Aout%20body;%0A>;%0Aout%20skel%20qt;&R'

print(lstvoltage)
print(df.iloc[0])
print("OK")

with open("voltage_table.html", "w") as text_file:
    text_file.write(htmlreturn)
