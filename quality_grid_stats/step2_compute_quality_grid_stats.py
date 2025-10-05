import geopandas as gpd
import pandas as pd
import networkx as nx
import json
import pprint
import config
from pathlib import Path


DATA_FOLDER = config.INPUT_GEODATA_FOLDER_PATH

from utils_json import json_save


def connectivity_analysis(graph):
    stats = {}
    list_graph_subsets = list(nx.connected_components(graph))
    graph_stats = []
    try:
        for l in list_graph_subsets:
            nbsub = len(
                [n for n in l if (graph.nodes[n]["grid_role"] == "substation") and (graph.nodes[n]["status"] != "disconnected")])
            nbseg = len([e for e in graph.subgraph(l).edges if graph.edges[e]["status"] != "disconnected"])
            if nbsub:
                graph_stats.append({"nbsub": nbsub, "nbseg": nbseg})
            """if nbsub<10 and nbsub and SHOW_SMALL_GRAPHSET:
                print(f"-- SECTION {nbsub} x {nbseg} :")
                [print(n, end=" | ") for n in l if
                 (graph.nodes[n]["grid_role"] == "substation") and (graph.nodes[n]["status"] != "disconnected")]
                print()"""

    except Exception:
        stats["substation_connectivity"] = -1
        stats["substation_connectivity_pct"] = -1
        return stats

    df_stat = pd.DataFrame(graph_stats)
    # stats["substation_connectivity_pct"] = "{:.1f}".format((max(df_stat["nbsub"]) / sum(df_stat["nbsub"]))*100)

    ## ANALYSIS OF GRID CONNECTIVITY
    if len(df_stat) == 0:
        stats["substation_connectivity"] = 0
        stats["substation_connectivity_pct"] = 0
    else:
        df_stat = df_stat.sort_values(["nbsub", "nbseg"], ascending=False)
        # Compute substation connectivity
        cumsum = 0
        for i, row in enumerate(df_stat.to_dict(orient='records')):
            cumsum += row["nbsub"] / (i + 1)
        stats["substation_connectivity_pct"] = cumsum / sum(df_stat["nbsub"])

        df_stat_text = df_stat["nbsub"].astype(str) + "x" + df_stat["nbseg"].astype(str)
        counts = df_stat_text.value_counts()
        stats["substation_connectivity"] = " + ".join(
            [f"{counts[subseg]}^({subseg})" if counts[subseg] != 1 else f"{subseg}"
             for subseg in df_stat_text.unique().tolist()])
    # print(counts)
    # stats["grid_connectivity"] = " + ". join(f"{x['nbsub']}x{x['nbseg']}" for x in df_stat.to_dict(orient='records'))

    #print("  -- Substation connectivity = ", stats["substation_connectivity"])
    #print("  -- Substation connectivity % = ", stats["substation_connectivity_pct"], "%")
    return stats

def main(country_code):
    df_power_line = gpd.read_file(f"{DATA_FOLDER}/{country_code}/osm_brut_power_line.gpkg")
    df_power_tower = gpd.read_file(f"{DATA_FOLDER}/{country_code}/osm_brut_power_tower_transition.gpkg")
    df_power_substation = gpd.read_file(f"{DATA_FOLDER}/{country_code}/osm_clean_power_substation.gpkg")
    df_pregraph_power_nodes = gpd.read_file(f"{DATA_FOLDER}/{country_code}/pre_graph_power_nodes.gpkg")
    df_pregraph_power_lines = gpd.read_file(f"{DATA_FOLDER}/{country_code}/pre_graph_power_lines.gpkg")
    gdf_postgraph_nodes = gpd.read_file(f"{DATA_FOLDER}/{country_code}/post_graph_power_nodes.gpkg")
    gdf_postgraph_lines = gpd.read_file(f"{DATA_FOLDER}/{country_code}/post_graph_power_lines.gpkg")

    gdf_postgraph_lines_circuit = gpd.read_file(f"{DATA_FOLDER}/{country_code}/post_graph_power_lines_circuit.gpkg")
    gdf_postgraph_nodes_circuit = gpd.read_file(f"{DATA_FOLDER}/{country_code}/post_graph_power_nodes_circuit.gpkg")

    G = nx.MultiGraph()
    gdf_postgraph_nodes.apply(lambda node: G.add_node(node["osmid"], grid_role=node["grid_role"],
                                            status=node["status"]), axis=1)
    gdf_postgraph_lines.apply(lambda line: G.add_edge(line["node0"], line["node1"], status= line["status"],
                                            osmid=line["osmid"]), axis=1)

    Gcircuit = nx.MultiGraph()
    gdf_postgraph_nodes_circuit.apply(lambda node: Gcircuit.add_node(node["osmid"], grid_role=node["grid_role"],
                                            status=node["status"]), axis=1)
    gdf_postgraph_lines_circuit.apply(lambda line: Gcircuit.add_edge(line["node0"], line["node1"], status= line["status"],
                                            osmid=line["osmid"]), axis=1)
    if not len(gdf_postgraph_lines):
        return

    mystat_classic = connectivity_analysis(G)
    mystat_circuit = connectivity_analysis(Gcircuit)

    # count nb connection substation <-> line
    nb_conn_line_sub = 0
    for node in G.nodes:
        mynode = G.nodes[node]
        if mynode["grid_role"] == "substation":
            nb_conn_line_sub += G.degree[node]
        else:
            pass


    with open(Path(config.OUTPUT_FOLDER_PATH) / "osmosestats" / f"{country_code}_osmose_stats.json") as f:
        data = json.load(f)

    sum_osmose = sum(list(data["class"].values()))
    if sum_osmose == 0:
        return

    ## Computing Health indicator
    names = {}
    indicators = {}
    explanations = {}


    key = "health_power_line_connectivity"
    names[key] = "Line connectivity"
    indicators[key] = len(gdf_postgraph_lines[gdf_postgraph_lines["status"] == "connected"]) / len(gdf_postgraph_lines)
    explanations[key] = "nb(Grid connected power line|cable) / nb(Grid power line|cable) || Grid line derivated (~=) from OSM power=line|cable after connectivity analysis"

    key = "health_grid_connectivity_without_circuit"
    names[key] = "Grid overall connectivity (without circuits)"
    indicators[key] = mystat_classic["substation_connectivity_pct"]
    explanations[key] = "Grid analysis"

    key = "health_grid_connectivity_with_circuit"
    names[key] = "Grid overall connectivity (with circuits)"
    indicators[key] = mystat_circuit["substation_connectivity_pct"]
    explanations[key] = "Grid analysis"

    key = "health_line_voltage_completeness"
    names[key] = "Voltage attribute completeness on power lines and cables"
    indicators[key] = len(df_power_line[df_power_line["voltage"].notnull()]) / len(df_power_line)
    explanations[key] =  "nb(OSM power=line|cable & voltage!='') /nb(OSM power=line|cable)"

    if len(df_power_line) > 0:
        key = "health_line_cables_completness"
        names[key] = "Cables attribute completeness on power lines and cables"
        indicators[key] = len(df_power_line[df_power_line["cables"].notnull()]) / len(df_power_line)
        explanations[key] =  "nb(OSM power=line|cable & cables!='') /nb(OSM power=line|cable)"

    if len(df_power_substation) > 0:
        key = "health_substation_voltage_completness"
        names[key] = "Voltage attribute completeness on substations"
        indicators[key] = len(df_power_substation[df_power_substation["voltage"].notnull()]) / len(df_power_substation)
        explanations[key] = "nb(OSM power=substation & voltage!='')/nb(OSM power=substation)"

    key = "health_connected_power_tower"
    names[key] = "Connected power tower (Osmose&nbsp;Class&nbsp;1)"
    indicators[key] = 1 - data["class-extend"]["nb_lone_power_tower"] / (len(df_power_tower[df_power_tower["power"]=="tower"]))
    explanations[key] = "1 - nb(Osmose-Class1-power=tower) / nb(OSM power=tower)"

    key = "health_complete_power_line"
    names[key] = "Complete power line (Osmose&nbsp;Class&nbsp;2)"
    indicators[key] = 1 - data["class"]["2"] / (len(df_power_line[df_power_line["power"]=="line"])*2)
    explanations[key] = "1 - nb(Osmose-Class2) / 2*nb(OSM power=line)"

    if len(df_pregraph_power_nodes[df_pregraph_power_nodes["grid_role"].isin(["to_international", "lambda_node"])]) > 0:
        key = "health_consistent_line_voltage_connection"
        names[key] = "Line voltage consistency (Osmose&nbsp;Class&nbsp;3)"
        indicators[key] = 1 - data["class"]["3"] / (len(df_pregraph_power_nodes[df_pregraph_power_nodes["grid_role"].isin(["to_international", "lambda_node"])]))
        explanations[key] = "1 - nb(Osmose-Class3) / nb(connection nodes) | Connection nodes computed by grid analysis"

    if nb_conn_line_sub > 0:
        key = "health_consistent_linesub_voltage_connection"
        names[key] = "Line-Substation voltage consistency (Osmose&nbsp;Class&nbsp;7)"
        indicators[key] = 1 - data["class"]["7"] / nb_conn_line_sub
        explanations[key] = "1 - nb(Osmose-Class7) / nb(line-sub connection) | Line-Sub connection computed by grid analysis"

    indicators_p = {key: max(min(round(100*val,1), 100), 0) for key, val in indicators.items()}

    output_data = []
    for key in indicators.keys():
        output_data.append({"key":key, "name":names.get(key, ""), "value":indicators_p.get(key, ""), "explain":explanations.get(key, "")})

    ## Computing Stats indicator
    names = {}
    indicators = {}
    explanations = {}

    key = "stats_nb_international_connections"
    names[key] = "Number of international connection"
    indicators[key] = len([n for n in G.nodes if G.nodes[n]["grid_role"] == "international"])
    explanations[key] = "..."

    key = "stats_nb_substations"
    names[key] = "Number of substations"
    indicators[key] = len([n for n in G.nodes if G.nodes[n]["grid_role"] == "substation"])
    explanations[key] = "..."

    key = "stats_line_voltages"
    names[key] = "Lines voltages"
    indicators[key] = df_power_line["voltage"].unique().tolist()
    explanations[key] = "..."

    for key in indicators.keys():
        output_data.append({"key":key, "name":names.get(key, ""), "value":indicators.get(key, ""), "explain":explanations.get(key, "")})

    #import pprint
    #pprint.pp(output_data)
    return output_data


if __name__ == "__main__":
    for countrycode in config.PROCESS_COUNTRY_LIST:
        myresult = main(countrycode)
        json_save(myresult, countrycode, "qgstats")

    if False:
        for ccode in config.WORLD_COUNTRY_DICT.keys():
            try:
                main(ccode)
                print(ccode)
            except Exception as e:
                print("Error with", ccode)
                pass