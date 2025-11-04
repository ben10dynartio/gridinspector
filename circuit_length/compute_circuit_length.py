import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent / "common"))

import configapps
from utils_exec import add_error, errors_to_file

OUTPUT_FOLDER_NAME = "circuit_length"

import json
import math

import geopandas as gpd
import pandas as pd
import numpy as np


def haversine_distance(coord1, coord2):
    """Calculates the distance between two lat/lon coordinates in kilometers."""
    lat1, lon1 = coord1
    lat2, lon2 = coord2
    R = 6371  # Earth radius in km
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) * math.sin(dlat / 2) +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlon / 2) * math.sin(dlon / 2))
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

def length_way(geometry) :
    coords = geometry.coords
    xc = [coord[0] for coord in coords]
    yc = [coord[1] for coord in coords]
    total_length = 0
    for i in range(len(coords) - 1):
        #from geopy import distance  => Take too much time, but more precise
        #total_length += distance.distance((yc[i], xc[i]), (yc[i+1], xc[i+1])).kilometers
        total_length += haversine_distance((yc[i], xc[i]), (yc[i+1], xc[i+1]))
    return total_length


def length_segment(args):
    y1, x1, y2, x2 = args
    return distance.distance((y1, x1), (y2, x2)).kilometers


def main(country_code):
    print(f"> Start computing circuit length - {country_code}")
    errors = []

    gdf = gpd.read_file(configapps.INPUT_GEODATA_FOLDER_PATH / f"{country_code}/osm_brut_power_line.gpkg").to_crs(epsg=4326)
    gdf["geom_type"] = gdf["geometry"].apply(lambda x: x.__class__.__name__)
    gdf = gdf[gdf["geom_type"] == "LineString"]


    print(" -- Managing voltage and circuit tags")
    # --------- Manage and check "circuit" tag as int --------------------
    gdf["circuits"] = gdf["circuits"].apply(lambda x: convert_int(x, default=1))
    gdf["circuits"] = np.where(gdf["circuits"]==-1,
                                     1, gdf["circuits"])
    maxcircuits = max(gdf['circuits'])
    print(f" -- Unique circuits value : {gdf["circuits"].unique().tolist()}")

    temp = gdf[gdf["circuits"]==0]
    for row in temp.to_dict(orient='records'):
        add_error(errors, {"name":"IncorrectCircuitNumber",
                           "description":f"The line have circuits = 0",
                           "osmid":f"way/{row['id']}"})
    gdf = gdf[gdf["circuits"] != 0]

    gdf["voltage"] = np.where(gdf["voltage"].isna(), "0", gdf["voltage"])
    gdf["voltage_list"] = gdf["voltage"].apply(lambda x: x.split(";"))
    gdf["nb_voltage"] = gdf["voltage_list"].apply(lambda x: len(x))

    """print("Somme = ", sum(gdf["line_length"]), "km")
    print("circuits values =", gdf["circuits"].unique().tolist())
    print("voltage values =", gdf["voltage"].unique().tolist())"""

    # :todo: Check inconsistency
    temp = gdf[(gdf["nb_voltage"]!=gdf["circuits"]) & (gdf["nb_voltage"]>=2)]
    for row in temp.to_dict(orient='records'):
        add_error(errors, {"name":"DifferentNumberVoltagesCircuits",
                           "description":f"The number of voltages [{row['voltage']}] is different of the number of circuits [{row['circuits']}]",
                           "osmid":f"way/{row['id']}"})
    gdf["circuits"] = np.where(gdf["nb_voltage"]>gdf["circuits"],
                               gdf["nb_voltage"], gdf["circuits"])
    gdf["voltage_list"] = np.where((gdf["nb_voltage"]<gdf["circuits"]) & (gdf["nb_voltage"] != 1),
                                   gdf.apply(lambda x: x["voltage_list"] + [0]*(x["circuits"] - x["nb_voltage"]), axis=1),
                                   gdf["voltage_list"])
    gdf["voltage_list"] = np.where(gdf["nb_voltage"] == 1,
                                   gdf.apply(lambda x: [x["voltage"],]*x["circuits"], axis=1),
                                   gdf["voltage_list"])
    gdf["nb_voltage"] = gdf["voltage_list"].apply(lambda x: len(x))

    print(" -- Computing line length")
    gdf["line_length"] = gdf["geometry"].apply(lambda x: length_way(x))

    ## Splitting voltages
    print(" -- Split by voltage")
    dfs = []
    for i in range(1, maxcircuits+1):
        mydf = gdf[gdf["circuits"]>=i].copy()
        mydf["voltage"] = mydf["voltage_list"].apply(lambda x: x[i-1])
        dfs.append(mydf)
    gdf = pd.concat(dfs)

    print(" -- Managing voltage tags as int")
    # --------- Manage and check "circuit" tag as int --------------------
    gdf["voltage_int"] = gdf["voltage"].apply(lambda x: convert_int(x, default=0))
    temp = gdf[gdf["voltage_int"]==-1]
    for row in temp.to_dict(orient='records'):
        add_error(errors, {"name": "VoltageValueError",
                           "description": f"The voltage [{row['voltage']}] is not valid",
                           "osmid": f"way/{row['id']}"})
    gdf["voltage"] = np.where(gdf["voltage_int"] == -1,
                              0, gdf["voltage_int"])

    lsv = gdf["voltage"].unique().tolist()
    lsv.sort()
    results = {}
    for v in lsv:
        tdf = gdf[gdf["voltage"]==v]
        key = str(round(v/1000,1)).replace(".0", "")
        results[key] = round(float(tdf["line_length"].sum()), 2)

    # Output Data
    myfolderpath = configapps.OUTPUT_FOLDER_PATH / OUTPUT_FOLDER_NAME
    myfolderpath.mkdir(exist_ok=True)
    output_filename = myfolderpath / f"{country_code}_circuit_length.json"
    with open(output_filename, "w") as file:
        json.dump(results, file)

    errors_to_file(errors, country_code, f"{country_code}_errors_compute_circuit_length.json")

    print(results)

def convert_int(value, default=0, error=-1):
    if type(value) is int:
        return value
    if value is None:
        return default
    if value == "":
        return default
    if value.isdigit():
        return int(value)
    return error

if __name__ == '__main__':
    for country in configapps.PROCESS_COUNTRY_LIST:
        main(country)
