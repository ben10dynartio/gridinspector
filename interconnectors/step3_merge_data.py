import pandas as pd
import geopandas as gpd
from common import (countrylist, overpass_query, overpass_response_to_gdf,
                    PATH_OVERPASSED_COUNTRIES, PATH_CONCAT_OVERPASSED_COUNTRIES)
import time
import logging

logging.basicConfig(
    filename='erreurs.log',  # Nom du fichier de log
    level=logging.DEBUG,  # Seuil de log (ici, on enregistre uniquement les erreurs et plus graves)
    format='%(asctime)s - %(levelname)s - %(message)s'  # Format du message
)
logging.getLogger().addHandler(logging.StreamHandler())  # Ajouter un second log dans la console (en plus du fichier) :

OSM_TAGS_WAY = ["name", "power", "voltage", "circuits", "cables", "wires", "operator", "operator:wikidata", "location",
                "note", "wikidata"]
INPUT_FILENAME = "../data/osm_crossborder_linecable_brut.gpkg"
OUTPUT_FILENAME = "../data/osm_connected_related_linecable"

MODE = "OUTPUT"  # OUTPUT, TEST, DEBUG
ACTIVE_LINKED = False
ACTIVE_RELATED = True
TEST_VALUE = [174097214]  # [542382059,626033399, 754698865, 257781200, 206138202]

RANGE_STEP = 450  # Number of ids for overpass query on ids, because they cannot all be requesting in once (query too large)


# way/174097214 is Finland-Estonia line/cable connection, with a relation set on the line & cable but not on substation endpoints
# way/144385755 in Portugal / Spain is making trouble ...
# node/7050352543 is making trouble
# way/453123241 not showing up

def main():
    gdf_conn = gpd.read_file(OUTPUT_FILENAME + "_connected_subpart.gpkg")
    gdf_rel = gpd.read_file(OUTPUT_FILENAME + "_related_subpart.gpkg")

    #gdf_rel["power"]

    ways_in_relation = set(gdf_rel["id"].unique().tolist())

    gdf_asso_in_rel = gdf_conn[gdf_conn["id"].isin(ways_in_relation)]
    crossborder_in_rel = set(gdf_asso_in_rel["crossborder_way_ids"].unique().tolist())

    gdf_asso_notin_rel = gdf_conn[~gdf_conn["id"].isin(ways_in_relation)]
    for index, row in gdf_asso_notin_rel.to_dict(orient='index').items():
        if row["crossborder_way_ids"] in crossborder_in_rel:
            if row["power"] == "substation":
                # print(
                #    f" -- Error, substation way/{row['id']} not connected to relation. See way/{row['crossborder_way_ids']}")
                logging.debug(
                    f" -- Error, substation https://openstreetmap.org/way/{row['id']} not connected to relation. See https://openstreetmap.org/way/{row['crossborder_way_ids']}")
                logging.debug(
                    f"    > way(id:{row['id']}, {row['crossborder_way_ids']});(._;._<;);(._;._>;);")
            else:
                # print(
                #    f" -- Error, line way/{row['id']} not connected to relation. See way/{row['crossborder_way_ids']}")
                logging.debug(
                    f" -- Error, line https://openstreetmap.org/way/{row['id']} not connected to relation. See https://openstreetmap.org/way/{row['crossborder_way_ids']}")
                logging.debug(
                    f"    > way(id:{row['id']}, {row['crossborder_way_ids']});(._;._<;);(._;._>;);")

    gdf = gpd.GeoDataFrame(pd.concat([gdf_asso_notin_rel, gdf_rel]), geometry="geometry")
    if MODE == "OUTPUT":
        gdf.to_file(OUTPUT_FILENAME + ".gpkg")
    if MODE == "TEST":
        gdf.to_file(OUTPUT_FILENAME + "_test.gpkg")

if __name__ == "__main__":
    main()