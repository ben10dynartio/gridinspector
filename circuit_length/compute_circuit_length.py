import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent / "common"))

import configapps
from utils_exec import add_error, errors_to_file
from utils_data import convert_int

OUTPUT_FOLDER_STATS_NAME = "circuit_length"
OUTPUT_FOLDER_GPKG_NAME = "transmission_layer"

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
        #from geopy import distance  # => Take too much time, but more precise
        #total_length += distance.distance((yc[i], xc[i]), (yc[i+1], xc[i+1])).kilometers
        total_length += haversine_distance((yc[i], xc[i]), (yc[i+1], xc[i+1]))
    return total_length


def length_segment(args):
    y1, x1, y2, x2 = args
    return distance.distance((y1, x1), (y2, x2)).kilometers


def main(country_code):
    print(f"> Start computing circuit length - {country_code}")
    errors = []

    filepath = configapps.INPUT_GEODATA_FOLDER_PATH / f"{country_code}"
    if configapps.SOURCE == "overpass":
        filepath = filepath / "osm_brut_power_line.gpkg"
    elif configapps.SOURCE == "podoma":
        filepath = filepath / "osm_pdm_power_lines.gpkg"

    gdf = gpd.read_file(filepath).to_crs(epsg=4326)
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

    # OSM way length above 50 kV
    tdf = gdf[gdf["voltage"]>=50000].copy()
    #tdf = tdf.groupby('id').first()
    tdf = tdf.groupby('id').agg(lambda x: ";".join(map(str, x)) if x.name == "voltage" else x.iloc[0])
    tdf = gpd.GeoDataFrame(tdf, geometry="geometry", crs="epsg:4326")

    total_km_above_50kv = int(sum(tdf["line_length"]))
    print(" -- Total_km_above_50kv =", total_km_above_50kv, "km /", len(tdf), "features")

    # Export transmission layer
    myfolderpath = configapps.OUTPUT_FOLDER_PATH / OUTPUT_FOLDER_GPKG_NAME
    myfolderpath.mkdir(exist_ok=True)
    output_filename = myfolderpath / f"{country_code}_osm_transmission_grid.gpkg"
    tdf.to_file(output_filename)

    data = {}
    data["circuit_length_kv_km"] = results
    data["osm_way_above_50kv_length_km"] = total_km_above_50kv
    data["transmission_voltages_kv"] = ";".join(list(results.keys()))

    # Output Data
    myfolderpath = configapps.OUTPUT_FOLDER_PATH / OUTPUT_FOLDER_STATS_NAME
    myfolderpath.mkdir(exist_ok=True)
    output_filename = myfolderpath / f"{country_code}_circuit_length.json"
    with open(output_filename, "w") as file:
        json.dump(data, file)

    errors_to_file(errors, country_code, f"{country_code}_errors_compute_circuit_length.json")

    #print(results)

if __name__ == '__main__':
    for country in configapps.PROCESS_COUNTRY_LIST:
        main(country)
