import pandas as pd
import geopandas as gpd
from common import (countrylist, overpass_query, overpass_response_to_gdf,
                    PATH_OVERPASSED_COUNTRIES, PATH_CONCAT_OVERPASSED_COUNTRIES)

import ast
import numpy as np
from shapely import geometry, ops, reverse


INPUT_FILENAME = "../data/osm_connected_related_linecable"
OUTPUT_FILENAME = "../data/interconnection_final.gpkg"

JOIN_KEY_LIST = ["power", "voltage"]

def main():
    gdf = gpd.read_file(INPUT_FILENAME + ".gpkg").fillna("")
    mycrs = gdf.crs

    #gdf = gdf[gdf["id"].isin([818568503, 203561365])]

    gdf["nodes"] = gdf["nodes"].map(ast.literal_eval)
    gdf["id_connection"] = np.where(gdf["id_rel"] == "",
                                    "way/" + gdf["crossborder_way_ids"],
                                    "relation/" + gdf["id_rel"].apply(lambda x: str(int(x)) if x else ''))
    gdf["node_start"] = gdf["nodes"].apply(lambda x: x[0])
    gdf["node_end"] = gdf["nodes"].apply(lambda x: x[-1])

    col = gdf.pop("id_connection")
    gdf.insert(0, col.name, col)

    gdf = gdf[gdf["power"] != "substation"]

    for joinkey in JOIN_KEY_LIST:
        gdf[joinkey] = gdf[joinkey].apply(lambda x: set([x]))

    unique_connections = gdf["id_connection"].unique().tolist()

    for p in gdf[gdf["node_start"] == gdf["node_end"]].to_dict(orient='records'):
        print(" -- Error, same node_start & node_end", p)

    dfconn = pd.DataFrame(gdf).sort_values("id_connection")

    # Processing merge of lines of same connections
    for conn in unique_connections:
        tempdf = dfconn[dfconn["id_connection"] == conn].copy()
        """for row in tempdf.to_dict(orient='records'):
            print(row["node_start"], "->", row["node_end"])"""

        nodes_list = tempdf["node_start"].tolist() + tempdf["node_end"].tolist()
        nodes_set_list = list(set(nodes_list))
        for node in nodes_set_list:
            # print("Analyse node =", node, "| amoung =", nodes_list)
            if nodes_list.count(node) == 2:
                tempgdf2 = tempdf[(tempdf["node_start"] == node) | (tempdf["node_end"] == node)].copy()
                z = [row for row in tempgdf2.to_dict(orient='records')]
                if len(z) == 1:
                    print(" -- Error with following row, only one record for node =", node, " | row = ", z)
                    for m in tempgdf2.to_dict(orient='records'):
                        print(m["node_start"], m["node_end"], m)
                else:
                    newrow = merge_two_rows(z[0], z[1], node)
                    tempdf = tempdf[(tempdf["node_start"] != node) & (tempdf["node_end"] != node)].copy()
                    tempdf = pd.concat([pd.DataFrame([newrow]), tempdf])
            elif (ct := nodes_list.count(node)) > 2:
                print(f" -- {ct} lines connected in one point : node/{node} ; lines = ", tempdf["id"].tolist())

        dfconn = pd.concat([dfconn[dfconn["id_connection"] != conn].copy(), tempdf])

    extremity_lines_nodes = list(set(dfconn["node_start"].tolist() + dfconn["node_end"].tolist()))
    node_country_dict = query_node_country_dict(extremity_lines_nodes)
    # print("Extremities lines = ", extremity_lines_nodes)

    for joinkey in JOIN_KEY_LIST:
        dfconn[joinkey] = dfconn[joinkey].apply(lambda x: ";".join(list(x)))

    gdf_fusion = gpd.GeoDataFrame(dfconn, geometry="geometry", crs=mycrs)
    gdf_fusion.to_file("interconnection_fusion_ways.gpkg")

    dfgrp = dfconn.groupby("id_connection").agg(custom_agg(dfconn.columns)).reset_index()
    # print(dfgrp.columns)
    dfgrp["extremity_nodes"] = (dfgrp["node_start"].str.split(";") + dfgrp["node_end"].str.split(";")).apply(
        lambda x: list(set(x)))
    dfgrp["countries"] = dfgrp["extremity_nodes"].apply(
        lambda x: list(set([node_country_dict.get(j) for j in x if j in node_country_dict])))
    dfgrp["nb_countries"] = dfgrp["countries"].map(len)
    for key_to_join in ["extremity_nodes", "countries"]:
        dfgrp[key_to_join] = dfgrp[key_to_join].apply(lambda x: ";".join(x))

    for key in ["node_start", "node_end", "tags", "type", "type_rel", "uid", "version", "user", "timestamp", "uid_rel",
                "version_rel", "user_rel", "timestamp_rel", "id", "osm_id"]:
        if key in dfgrp:
            del dfgrp[key]
    gdf_fusion = gpd.GeoDataFrame(dfgrp, geometry="geometry", crs=mycrs)
    gdf_fusion.to_file("interconnection_fusion_full.gpkg")

    gdf_fusion = gdf_fusion[gdf_fusion["nb_countries"] >= 2]
    gdf_fusion.to_file(OUTPUT_FILENAME)

### SUPPORT FUNCTIONS #####################################################################
def merge_two_rows(row1, row2, nodeid, log_level='INFO'):
    #print(f' -- Merge : row1 ({row1["node_start"]}>{row1["node_end"]}) / row2 ({row2["node_start"]}>{row2["node_end"]})')
    if (row1["node_start"] == nodeid) and (row2["node_start"] == nodeid):
        #row 1 is reverse, row 2 added
        myrow = row1.copy()
        myrow["nodes"] = list(reversed(row1["nodes"])) + row2["nodes"]
        # combine them into a multi-linestring
        multi_line = geometry.MultiLineString([reverse(row1["geometry"]), row2["geometry"]])
        myrow["geometry"] = ops.linemerge(multi_line)
        myrow["node_start"] = row1["node_end"]
        myrow["node_end"] = row2["node_end"]
    elif (row1["node_start"] != nodeid) and (row2["node_start"] == nodeid):
        #normally connected, row1 + row2
        myrow = row1.copy()
        myrow["nodes"] = row1["nodes"] + row2["nodes"]
        # combine them into a multi-linestring
        multi_line = geometry.MultiLineString([row1["geometry"], row2["geometry"]])
        myrow["geometry"] = ops.linemerge(multi_line)
        myrow["node_start"] = row1["node_start"]
        myrow["node_end"] = row2["node_end"]
    elif (row1["node_start"] == nodeid) and (row2["node_start"] != nodeid):
        #normally connected, row2 + row1 both reverde
        myrow = row2.copy()
        myrow["nodes"] = row2["nodes"] + row1["nodes"]
        # combine them into a multi-linestring
        multi_line = geometry.MultiLineString([row2["geometry"], row1["geometry"]])
        myrow["geometry"] = ops.linemerge(multi_line)
        myrow["node_start"] = row2["node_start"]
        myrow["node_end"] = row1["node_end"]
    elif (row1["node_start"] != nodeid) and (row2["node_start"] != nodeid):
        #Connected at the end : row 1 starts, row 2 is reversed and added
        myrow = row1.copy()
        myrow["nodes"] = row1["nodes"] + list(reversed(row2["nodes"]))
        # combine them into a multi-linestring
        multi_line = geometry.MultiLineString([row1["geometry"], reverse(row2["geometry"])])
        myrow["geometry"] = ops.linemerge(multi_line)
        myrow["node_start"] = row1["node_start"]
        myrow["node_end"] = row2["node_start"]
    else:
        raise ValueError
    myrow["id"] = str(row1["id"]) + ";" + str(row2["id"])
    #print(row1["power"], row2["power"])
    myrow["power"] = row1["power"].union(row2["power"])
    #print("    |-> ", myrow["node_start"], " -> ", myrow["node_end"])
    return myrow


def query_node_country_dict(nodelist, log_level='INFO', range_step=500):
    return_dict= {}
    for i in range(0, len(nodelist), range_step):
        nodestr = ",".join([f"{j}" for j in nodelist[i:i+range_step]])
        query = f"""
        [out:json][timeout:25]; 
        node(id:{nodestr});
        foreach -> .unode {{
            .unode is_in;
            area._[admin_level="2"]["ISO3166-1:alpha2"];
        
            convert Feature
                country_name = t["name"],
                country_code = t["ISO3166-1:alpha2"],
                node_id = unode.u(id());
            (._;.allset;)->.allset;
        }}
        .allset;
        out;
        """
        if log_level in ["INFO", "DEBUG"]: print(query)
        response = overpass_query(query)
        return_dict = {**return_dict,
                       **{el["tags"]["node_id"]:el["tags"]["country_code"] for el in response['elements']}}
    return return_dict


def fusion_multiline(x):
    try:
        ret = geometry.MultiLineString(list(x))
    except TypeError:
        print("Error with geometry :", x)
        return list(x)[0]
    return ret


# Fonction d'agrégation
def custom_agg(columns):
    aggdict = {
        'geometry': lambda x: fusion_multiline(x),
    }
    for col in columns:
        if col not in ['geometry', 'id_connection']:
            aggdict[col] = lambda x: ";".join(list(set(map(str, list(x)))))
    return aggdict
    #** {col: lambda x: x[col] for col in dfconn.columns if col not in ['node_start', 'geometry', 'id_connection']}

if __name__ == "__main__":
    main()
