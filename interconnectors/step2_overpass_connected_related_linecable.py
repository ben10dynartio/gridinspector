import pandas as pd
import geopandas as gpd
from common import (countrylist, overpass_query, overpass_response_to_gdf,
                    PATH_OVERPASSED_COUNTRIES, PATH_CONCAT_OVERPASSED_COUNTRIES)
import time
import logging

logging.basicConfig(
    filename='erreurs.log',               # Nom du fichier de log
    level=logging.DEBUG,                  # Seuil de log (ici, on enregistre uniquement les erreurs et plus graves)
    format='%(asctime)s - %(levelname)s - %(message)s'  # Format du message
)
logging.getLogger().addHandler(logging.StreamHandler()) #Ajouter un second log dans la console (en plus du fichier) :

OSM_TAGS_WAY = ["name", "type", "route", "power", "voltage", "circuits", "cables", "wires", "operator", "operator:wikidata", "location", "note", "wikidata"]
INPUT_FILENAME = "../data/osm_crossborder_linecable_brut.gpkg"
OUTPUT_FILENAME = "../data/osm_connected_related_linecable"

MODE = "OUTPUT" # OUTPUT, TEST, DEBUG
ACTIVE_LINKED = True # Set to true for retreiving all
ACTIVE_RELATED = True # Set to true for retreiving all
TEST_VALUE = [174097214] # [542382059,626033399, 754698865, 257781200, 206138202]

RANGE_STEP = 450 # Number of ids for overpass query on ids, because they cannot all be requesting in once (query too large)

# way/174097214 is Finland-Estonia line/cable connection, with a relation set on the line & cable but not on substation endpoints
# way/144385755 in Portugal / Spain is making trouble ...
# node/7050352543 is making trouble
# way/453123241 not showing up

def main():
    # get step 1 result (crossing border ways) and init way_ids_list
    crossborder_linecables = gpd.read_file(INPUT_FILENAME)
    way_ids_list = crossborder_linecables["id"].unique().tolist()
    if MODE == "TEST":
        way_ids_list = TEST_VALUE

    # get all connected ways (if it is unique way connected to the cross-border line)
    if ACTIVE_LINKED:
        mygdf_asso = [query_linked_ways(way_ids_list[i:i + RANGE_STEP], log_level='DEBUG') for i in
                      range(0, len(way_ids_list), RANGE_STEP)]
        if mygdf_asso[0] is not None:
            mygdf_asso = gpd.GeoDataFrame(pd.concat(mygdf_asso), geometry="geometry", crs=4326)
            if MODE == "OUTPUT":
                mygdf_asso.to_file(OUTPUT_FILENAME + "_connected_subpart.gpkg")
            if MODE == "TEST":
                mygdf_asso.to_file(OUTPUT_FILENAME + "_connected_subpart_test.gpkg")
        #mygdf_asso = gpd.read_file(OUTPUT_FILENAME + "_connected_subpart.gpkg")
        print("-- query on linked way performed")

    # Get all relation linked to ways
    if ACTIVE_RELATED:
        ways_in_relation = set()
        mygdf_rel_tab = [query_related_ways(way_ids_list[i:i + RANGE_STEP], log_level='INFO') for i in
                     range(0, len(way_ids_list), RANGE_STEP)]
        if mygdf_rel_tab[0] is not None:
            mygdf_rel = gpd.GeoDataFrame(pd.concat(mygdf_rel_tab), geometry="geometry", crs=4326)
            if MODE == "OUTPUT":
                mygdf_rel.to_file(OUTPUT_FILENAME + "_related_subpart.gpkg")
            if MODE == "TEST":
                mygdf_rel.to_file(OUTPUT_FILENAME + "_related_subpart_test.gpkg")
            # mygdf_rel = gpd.read_file(OUTPUT_FILENAME + "_related_subpart.gpkg")

            ways_in_relation = set(mygdf_rel["id"].unique().tolist())
        print("-- query on related way performed")



def query_linked_ways(way_ids, log_level="ERROR"):
    str_way = ",".join([f"{id}" for id in way_ids])

    query = """
    [out:json][timeout:300]; 
    way(id:%s)->.setw;
    
    foreach.setw {
      ._->.initset;
      ._-> .z;
      ()->.outforeach;
      node(w:1,-1)->.extremity_nodes;
      foreach.extremity_nodes (
        ._->.allconnectednodes;
        complete.initset->.myways {
          way["power"~"^(line|cable)$"](bn.allconnectednodes)->.allconnectedways;
          (.allconnectedways; - .initset;) -> .newways;
          if (newways.count(ways) == 1) {
            .allconnectedways -> .initset;
            (node(w.newways:1,-1); .allconnectednodes;)-> .allconnectednodes;
          }
        }
        (.initset;.outforeach;)->.outforeach;
       )
       
      node(w.outforeach:1,-1)->.extnodes;
      .extnodes is_in -> .someArea;
      way[power=substation](pivot.someArea)->.aroundways;
		
       %s
    };
    .allset;
    
    out meta geom;
    """

    # Use this part to get geometric shape (standard behavior)
    geom_query_supp = """
    (.allset;.outforeach;.aroundways;)->.allset;
    """

    # Use this part for requesting the link between each way, and the cross-border way 
    asso_query_supp = """
    (.outforeach;.aroundways;)->.myset;
    foreach.myset {
        convert Feature
        //::=::,
        //::id = _.u(id()),
        //::geom=geom(),
        original_way_id = _.u(id()),
        associated_way_id = z.u(id());
        (._;.allset;)->.allset;
      } 
      """

    myquery = query % (str_way, geom_query_supp)
    if log_level in ["DEBUG"]: print(myquery)
    response_geom = overpass_query(myquery)
    gdf = overpass_response_to_gdf(response_geom, tags=OSM_TAGS_WAY)
    gdf["id"] = gdf["id"].astype(int)
    """response_asso = overpass_query(query % (str_way, asso_query_supp))
    dict_asso = {d["id"]:int(d["tags"]["associated_way_id"]) for d in response_asso['elements']}
    gdf["associated_way_id"] = gdf["id"].apply(lambda x: dict_asso[x])"""

    myquery = query % (str_way, asso_query_supp)
    if log_level in ["DEBUG"]: print(myquery)
    response_asso = overpass_query(myquery)
    df_asso = pd.DataFrame([{"original_way_id": int(d["tags"]["original_way_id"]),
                             "crossborder_way_ids": int(d["tags"]["associated_way_id"])}
                            for d in response_asso['elements']])
    df_asso = df_asso.sort_values("crossborder_way_ids")
    df_asso = df_asso.groupby("original_way_id").agg(list).reset_index()
    df_asso["crossborder_way_ids"] = df_asso["crossborder_way_ids"].apply(lambda x: ";".join([str(y) for y in x]))
    gdf = gdf.merge(df_asso, left_on="id", right_on="original_way_id")
    del gdf["original_way_id"]
    if log_level in ["INFO", "DEBUG"]: print("request connected done")
    time.sleep(10)
    return gdf


def query_related_ways(way_ids, log_level="ERROR"):
    str_way = ",".join([f"{id}" for id in way_ids])

    query = """
    [out:json][timeout:300]; 
    way(id:%s)->.setw;
    (rel[power=circuit](bw.setw);rel[route=power](bw.setw);)->.rels;

    foreach.rels -> .onerel (
        %s
    );
    .allset;
    out meta geom;
    """

    # Use this part to get geometric shape (standard behavior)
    geom_query_supp = """
    (way(r.onerel);.allset;)->.allset;
    """

    # Use this part for requesting the link between each way, and the cross-border way
    asso_relway_query_supp = """
        way(r.onerel);
            foreach {
                convert Feature
                //::=::,
                //::id = _.u(id()),
                //::geom=geom(),
                original_way_id = _.u(id()),
                associated_rel_id = onerel.u(id());
                //associated_rel_name = onerel["name"];
                (._;.allset;)->.allset;
              } 
          """

    query_rel_only = """
        [out:json][timeout:300]; 
        way(id:%s)->.setw;
        (rel[power=circuit](bw.setw);rel[route=power](bw.setw););
        out meta geom;
        """

    # Relation : type=route & route=power OR type=power & power=circuit
    myquery = query % (str_way, geom_query_supp)
    if log_level in ["DEBUG"]: print(myquery)
    response_geom = overpass_query(myquery)
    gdf = overpass_response_to_gdf(response_geom, tags=OSM_TAGS_WAY)
    gdf["id"] = gdf["id"].astype(int)

    myquery = query % (str_way, asso_relway_query_supp)
    if log_level in ["DEBUG"]: print(myquery)
    response_asso_relway = overpass_query(myquery)
    df_asso_relway = pd.DataFrame([{"original_way_id":int(d["tags"]["original_way_id"]),
                          "associated_rel_id":int(d["tags"]["associated_rel_id"])}
                         for d in response_asso_relway['elements']])
    if len(df_asso_relway)==0:
        return None
    gdf = gdf.merge(df_asso_relway, left_on="id", right_on="original_way_id")

    dfcopy = gdf[gdf["id"].isin(way_ids)].copy().sort_values("original_way_id")
    dictres = {}
    print("len of dfcopy", len(dfcopy))
    for relid in dfcopy["associated_rel_id"].unique().tolist():
        temp = dfcopy[dfcopy["associated_rel_id"]==relid]
        ls = ";".join([str(y) for y in temp["original_way_id"].unique().tolist()])
        dictres[relid] = ls

    gdf["crossborder_way_ids"] = gdf["associated_rel_id"].apply(lambda x: dictres[x])
    del gdf["original_way_id"]

    myquery = query_rel_only % (str_way)
    if log_level in ["DEBUG"]: print(myquery)
    response_geom = overpass_query(myquery)
    gdfrel = overpass_response_to_gdf(response_geom, tags=OSM_TAGS_WAY)
    dfrel = pd.DataFrame(gdfrel)
    del dfrel["geometry"]
    dfrel["id"] = dfrel["id"].astype(int)

    gdf = gdf.merge(dfrel, how="left" , left_on="associated_rel_id", right_on="id", suffixes=(None, '_rel'),)
    if log_level in ["INFO", "DEBUG"]: print("request related done")
    time.sleep(10)
    return gdf

if __name__ == "__main__":
    main()