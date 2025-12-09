import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent / "common"))

import configapps

import geopandas as gpd
import ast
from pathlib import Path

import pandas as pd

lineres = []
subres = []

def to_int(x):
    try:
        return int(x)
    except ValueError:
        print("Error with voltage =", x)
        return -1


for countrykey, countryname in configapps.WORLD_COUNTRY_DICT.items():
    print("reading", countrykey, countryname)
    dfline = gpd.read_file(f"/home/ben/DevProjects/osm-power-grid-map-analysis/data/{countrykey}/osm_brut_power_line.gpkg")
    dfsub = gpd.read_file(f"/home/ben/DevProjects/osm-power-grid-map-analysis/data/{countrykey}/osm_brut_power_substation.gpkg")

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



    rowline = {"Country Code":countrykey, "Country Name":countryname, "Nb items":len(dfline),
               "Line voltage":str(lineset["voltage"]),
               "Line Operator":str(lineset["operator"]), "Line Operator Wikidata":str(lineset["operator:wikidata"])}
    rowsub = {"Country Code": countrykey, "Country Name": countryname, "Nb items":len(dfsub),
              "Line voltage": str(subset["voltage"]),
              "Line Operator": str(subset["operator"]), "Line Operator Wikidata": str(subset["operator:wikidata"])}

    lineres.append(rowline)
    subres.append(rowsub)

dfline = pd.DataFrame(lineres)
dfsub = pd.DataFrame(subres)

dfline.to_excel("osm_country_data_power_line.xlsx")
dfsub.to_excel("osm_country_data_power_substation.xlsx")