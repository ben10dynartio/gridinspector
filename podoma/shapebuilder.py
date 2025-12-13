import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent / "common"))

import configapps

import os
import argparse
import ast
import psycopg2
from psycopg2.extras import register_hstore

import geopandas as gpd
from shapely import wkb
from shapely.geometry import LineString

parser = argparse.ArgumentParser()
parser.add_argument("-c", "--country", type=str, help="Country OSM code", default="80500")
parser.add_argument("-d", "--date", type=str, help="Country OSM code", default="CURRENT_TIMESTAMP")

args = parser.parse_args()
datebuild = args.date
countryosmcode = args.country
#80500

# ---------------------------------------------
# Connect to PostgreSQL/PostGIS database
# ---------------------------------------------
dbname=os.getenv("PODOMA_DBNAME", "podoma")
user=os.getenv("PODOMA_DBUSER", "podoma")
password=os.getenv("PODOMA_DBPASS", "podomapass")
host=os.getenv("PODOMA_DBHOST", "localhost")
port=os.getenv("PODOMA_DBPORT", "5432")

print("Querying on ", dbname, "on", host)

conn = psycopg2.connect(
    dbname=dbname,
    user=user,
    password=password,
    host=host,
    port=port,
)

register_hstore(conn)


query = f"""
WITH lines AS (
    SELECT fc.osmid osmid, fc.version version, fc.tags wtags, fc.userid wuserid
    FROM pdm_features_lines_changes fc
    JOIN pdm_features_lines_boundary fb ON fc.osmid=fb.osmid AND fc.version=fb.version
    WHERE fb.boundary={countryosmcode}
    AND (({datebuild} >= fc.ts_start AND {datebuild} < fc.ts_end) OR ({datebuild} >= fc.ts_start AND fc.ts_end is null))
), nodesid AS (
    SELECT fm.memberid osmid, fm.osmid memberof, fm.pos pos, lines.wtags wtags, lines.wuserid wuserid
    FROM pdm_members_lines fm
    JOIN lines ON fm.osmid=lines.osmid AND fm.version=lines.version
), nodes AS (
    SELECT fc.osmid osmid, fc.geom geom, nid.memberof memberof, nid.pos pos, nid.wtags wtags, nid.wuserid wuserid
    FROM pdm_features_lines_changes fc
    JOIN nodesid nid ON fc.osmid=nid.osmid
    WHERE (({datebuild} >= fc.ts_start AND {datebuild} < fc.ts_end) OR ({datebuild} >= fc.ts_start AND fc.ts_end is null))
), supports AS (
    SELECT fc.osmid osmid, fc.tags tags, fc.userid nuserid
    FROM pdm_features_supports_changes fc
    JOIN pdm_features_supports_boundary fb ON fc.osmid=fb.osmid AND fc.version=fb.version
    WHERE fb.boundary={countryosmcode}
    AND (({datebuild} >= fc.ts_start AND {datebuild} < fc.ts_end) OR ({datebuild} >= fc.ts_start AND fc.ts_end is null))
), joined AS (
    SELECT nodes.osmid osmid, nodes.geom geometry, supports.tags ntags, nodes.memberof memberof, nodes.pos pos, nodes.wtags wtags, nodes.wuserid wuserid, supports.nuserid nuserid
    FROM nodes
    LEFT JOIN supports ON nodes.osmid=supports.osmid
)
SELECT * FROM joined;
"""

# ---------------------------------------------
# Load data into a GeoDataFrame
# ---------------------------------------------
OSM_POWER_TAGS = ["ref", "name", "type", "route", "power", "voltage", "substation", "line", "circuits", "cables", "wires", "operator", "operator:wikidata", "location", "note", "wikidata", "topology", "frequency", "line_management"]

output_path = configapps.OUTPUT_FOLDER_PATH / "pgsql"
output_path.mkdir(exist_ok=True, parents=True)

gdf = gpd.GeoDataFrame.from_postgis(query, conn, geom_col='geometry')
#gdf = gpd.read_file("/home/ben/DevProjects/temp/databox/pgsql/pdm_extract_points.gpkg")

def convert_dict(value):
    if value is None :
        return {}
    elif type(value) is str:
        return ast.literal_eval(value)
    elif type(value) is dict:
        return value
    else:
        raise ValueError(f"Unknown value type : {value}")


# Line Management
def agg_group_to_lines(g):
    first_row = g.iloc[0].copy()
    try:
        first_row["geometry"] = LineString(g["geometry"].apply(lambda p: (p.x, p.y)))
    except Exception:
        first_row["geometry"] = LineString()
    first_row["nodes"] = list(g["osmid"].apply(lambda x: int(x[5:])))
    return first_row

gdf_lines : gpd.GeoDataFrame = gdf.sort_values(["memberof", "pos"])
gdf_lines = gdf_lines.groupby("memberof").apply(agg_group_to_lines).reset_index(drop=True)
gdf_lines = gdf_lines.set_crs(gdf.crs)
gdf_lines["tags"] = gdf_lines["wtags"].map(convert_dict)
for tag in OSM_POWER_TAGS:
    gdf_lines[tag] = gdf_lines["tags"].apply(lambda x: x.pop(tag, None))
gdf_lines["osmid"] = gdf_lines["memberof"]
gdf_points["id"] = gdf_points["osmid"].apply(lambda x: int(x[5:]))
del gdf_lines["memberof"]
del gdf_lines["ntags"]
del gdf_lines["wtags"]
del gdf_lines["pos"]
print(gdf_lines)

# Export to a shapefile
output_path_lines = output_path / f"pdm_rebuild_lines.gpkg"
gdf_lines.to_file(output_path_lines)
print("Shapefile created:", output_path_lines)


# Points Management
def agg_group_to_points(g):
    first_row = g.iloc[0].copy()
    return first_row

gdf_points : gpd.GeoDataFrame = gdf.sort_values(["memberof", "pos"])
gdf_points = gdf_points.groupby("osmid").apply(agg_group_to_points).reset_index(drop=True)
gdf_points = gdf_points.set_crs(gdf.crs)
gdf_points["id"] = gdf_points["osmid"].apply(lambda x: int(x[5:]))
gdf_points["tags"] = gdf_points["ntags"].map(convert_dict)
for tag in OSM_POWER_TAGS:
    gdf_points[tag] = gdf_points["tags"].apply(lambda x: x.pop(tag, None))
del gdf_points["memberof"]
del gdf_points["ntags"]
del gdf_points["wtags"]
print(gdf_points)

# Export to a shapefile
output_path_points = output_path / f"pdm_rebuild_points.gpkg"
gdf_points.to_file(output_path_points)
print("Shapefile created:", output_path_points)