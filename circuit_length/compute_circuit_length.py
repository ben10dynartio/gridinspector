import json

import geopandas as gpd
import pandas as pd
import numpy as np
import math
from geopy import distance

from utils_exec import add_error, errors_to_file

import config

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
        total_length += distance.distance((yc[i], xc[i]), (yc[i+1], xc[i+1])).kilometers
    return total_length


def main(country_code):
    errors = []

    gdf = gpd.read_file(config.INPUT_GEODATA_FOLDER_PATH / f"{country_code}/osm_brut_power_line.gpkg").to_crs(epsg=4326)

    gdf["line_length"] = gdf["geometry"].apply(lambda x: length_way(x)) # Time consuming !

    gdf["circuits"] = gdf["circuits"].str.replace("!",'1')
    gdf["circuits"] = np.where(gdf["circuits"].isna(), '1', gdf["circuits"]).astype(int)

    gdf["voltage"] = np.where(gdf["voltage"].isna(), "", gdf["voltage"])
    gdf["nb_voltage"] = gdf["voltage"].apply(lambda x: x.count(";") + 1)
    gdf["nb_voltage"] = np.where(gdf["voltage"] == "", 0, gdf["nb_voltage"])

    """print("Somme = ", sum(gdf["line_length"]), "km")
    print("circuits values =", gdf["circuits"].unique().tolist())
    print("voltage values =", gdf["voltage"].unique().tolist())"""

    # :todo: Check inconsistency
    temp = gdf[(gdf["nb_voltage"]!=gdf["circuits"]) & (gdf["nb_voltage"]>=2)]
    for row in temp.to_dict(orient='records'):
        add_error(errors, {"name":"DifferentNumberVoltagesCircuits",
                           "description":"The number of voltages is different of the number of circuits",
                           "osmid":f"way/{row['id']}"})
    # Not reliable
    #gdf["circuits"] = np.where(gdf["nb_voltage"] == 2, 2, gdf["circuits"])

    ## Splitting voltages
    append_rows = []
    for row in gdf.to_dict(orient='records'):
        for i in range(2, max(gdf["circuits"])):
            if row["nb_voltage"] >= i:
                #print(row)
                temp = row.copy()
                temp["voltage"] = temp["voltage"].split(";")[i-1]
                append_rows.append(temp)

    gdf["voltage"] = np.where(gdf["nb_voltage"] == 2, gdf["voltage"].apply(lambda x: x.split(";")[0]), gdf["voltage"])

    if len(append_rows) > 0:
        gdf = pd.concat([gdf, gpd.GeoDataFrame(append_rows, geometry="geometry", crs=gdf.crs)])

    gdf["voltage"] = np.where(gdf["voltage"].apply(lambda x: "." in x), "0", gdf["voltage"])
    gdf["voltage"] = np.where(gdf["voltage"] == "", 0, gdf["voltage"]).astype(int)

    """print("Somme = ", sum(gdf["line_length"]), "km")
    print("circuits values =", gdf["circuits"].unique().tolist())
    print("voltage values =", gdf["voltage"].unique().tolist())
    print("voltage values =", gdf["voltage"].unique().tolist())"""

    gdf["circuit_length"] = gdf["line_length"] * gdf["circuits"]

    lsv = gdf["voltage"].unique().tolist()
    lsv.sort()
    results = {}
    for v in lsv:
        tdf = gdf[gdf["voltage"]==v]
        results[int(v/1000)] = round(float(tdf["circuit_length"].sum()), 2)

    output_filename = config.OUTPUT_FOLDER_PATH / f"{country_code}_circuit_length.json"
    with open(output_filename, "w") as file:
        json.dump(results, file)

    errors_to_file(errors, country_code, f"{country_code}_errors_compute_circuit_length.json")

if __name__ == '__main__':
    for country in config.PROCESS_COUNTRY_LIST:
        main(country)
