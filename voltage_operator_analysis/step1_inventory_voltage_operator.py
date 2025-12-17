import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent / "common"))

import configapps

import geopandas as gpd
import ast
from pathlib import Path
import json
import pandas as pd

FOLDERNAME = "voltageoperator"

lineres = []
subres = []

def to_int(x):
    try:
        return int(x)
    except ValueError:
        print("Error with voltage =", x)
        return -1

def main(countrykey):

    filepath = configapps.INPUT_GEODATA_FOLDER_PATH / f"{countrykey}"
    if configapps.SOURCE == "overpass":
        dfline = gpd.read_file(filepath / "osm_brut_power_line.gpkg")
        dfsub = gpd.read_file(filepath / "osm_brut_power_substation.gpkg")
    elif configapps.SOURCE == "podoma":
        dfline = gpd.read_file(filepath / "osm_pdm_power_lines.gpkg")
        dfsub = gpd.read_file(filepath / "osm_pdm_power_substations.gpkg")

    if len(dfline) == 0:
        print("-- No line")
    else:
        dfline["tagsdict"] = dfline["tags"].apply(lambda x: ast.literal_eval(x))
    if len(dfsub) == 0:
        print("-- No sub")
    else:
        dfsub["tagsdict"] = dfsub["tags"].apply(lambda x: ast.literal_eval(x))

    lineset = {}
    subset = {}

    for tagkey in ["voltage", "operator", "operator:wikidata"]:
        if len(dfline) != 0:
            dfline[tagkey] = dfline["tagsdict"].apply(lambda x: x.get(tagkey))
            mylist = dfline[tagkey].unique().tolist()
            if tagkey == "voltage":
                listoflist = [m.split(";") for m in mylist if m]
                mylist = sum(listoflist, [])
                mylist = [to_int(m) for m in mylist]
                mylist = list(set(mylist))
                mylist.sort()
        else:
            mylist = []
        lineset[tagkey] = list(set(mylist))
        if tagkey == "voltage":
            lineset[tagkey].sort()
        if len(dfsub) != 0:
            dfsub[tagkey] = dfsub["tagsdict"].apply(lambda x: x.get(tagkey))
            mylist = dfsub[tagkey].unique().tolist()
            if tagkey == "voltage":
                listoflist = [m.split(";") for m in mylist if m]
                mylist = sum(listoflist, [])
                mylist = [to_int(m) for m in mylist]
                mylist = list(set(mylist))
                mylist.sort()
        else:
            mylist = []
        subset[tagkey] = list(set(mylist))
        if tagkey == "voltage":
            subset[tagkey].sort()

    row = {"codeiso2": countrykey,
           "nb_line": len(dfline),
           "line_voltage": lineset["voltage"],
           "line_operator": lineset["operator"],
           "line_operator_wikidata": lineset["operator:wikidata"],
           "nb_substation": len(dfsub),
           "substation_voltage": subset["voltage"],
           "substation_operator": subset["operator"],
           "substation_operator_wikidata": subset["operator:wikidata"]}

    filefolder = configapps.OUTPUT_FOLDER_PATH / FOLDERNAME
    filefolder.mkdir(exist_ok=True, parents=True)
    with open(filefolder / f"{countrykey}_voltage_operator.json", "w",
              encoding="utf-8") as f:
        json.dump(row, f, ensure_ascii=False, indent=4)

if __name__ == "__main__":
    for country_code in configapps.PROCESS_COUNTRY_LIST:
        main(country_code)