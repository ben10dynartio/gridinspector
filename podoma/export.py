import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent / "common"))

import configapps

import os
import argparse
import psycopg2
from psycopg2.extras import register_hstore

import geopandas as gpd
from shapely import wkb

parser = argparse.ArgumentParser()
parser.add_argument("-t", "--objecttype", type=str, help="Object Type", default="lines")
parser.add_argument("-c", "--country", type=str, help="Country OSM code", default="80500")

args = parser.parse_args()
countryosmcode = args.country
objecttype = args.objecttype
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

query_dict = {}

query = """
    SELECT *, ST_AsBinary(geom) AS geom_wkb
    FROM pdm_boundary LIMIT 20;
"""

query_dict["countryshapes"] = """
    SELECT * AS geom_wkb
    FROM pdm_boundary WHERE admin_level = 2;
"""

query_dict["lines"]  = f"""
SELECT fc.osmid, fc.version, fc.tags, fl.label, fc.geom_len, fc.geom FROM pdm_features_lines_changes fc
JOIN pdm_features_lines_boundary fb ON fb.osmid=fc.osmid AND fb.version=fc.version
JOIN pdm_features_lines_labels fl ON fl.osmid=fc.osmid AND fl.version=fc.version
WHERE fb.boundary = {countryosmcode}
AND fc.geom_len <> 0 
AND fl.label='transmission'
AND (CURRENT_TIMESTAMP BETWEEN fc.ts_start AND fc.ts_end OR (CURRENT_TIMESTAMP >= fc.ts_start AND fc.ts_end is null));
        """

query_dict["points"]  = f"""
SELECT fm.memberid, fs.version, fs.tags, fs.geom FROM pdm_members_lines fm
JOIN pdm_features_lines_boundary fb ON fm.osmid=fb.osmid AND fm.version=fb.version
JOIN pdm_features_lines_changes fc ON fc.osmid=fm.osmid AND fc.version=fm.version
LEFT JOIN pdm_features_supports_changes fs ON fm.memberid=fs.osmid AND fc.version=fs.version
WHERE fb.boundary = {countryosmcode}
AND (CURRENT_TIMESTAMP BETWEEN fc.ts_start AND fc.ts_end OR (CURRENT_TIMESTAMP >= fc.ts_start AND fc.ts_end is null))
AND (CURRENT_TIMESTAMP BETWEEN fs.ts_start AND fs.ts_end OR (CURRENT_TIMESTAMP >= fs.ts_start AND fs.ts_end is null));
"""

query_dict["substations"]  = f"""
SELECT fc.osmid, fc.version, fc.tags, fc.geom  FROM pdm_features_substations_changes fc
JOIN pdm_features_substations_boundary fb ON fc.osmid=fb.osmid AND fc.version=fb.version
WHERE fb.boundary = {countryosmcode}
AND (CURRENT_TIMESTAMP BETWEEN fc.ts_start AND fc.ts_end OR (CURRENT_TIMESTAMP >= fc.ts_start AND fc.ts_end is null));
"""

# ---------------------------------------------
# Load data into a GeoDataFrame
# ---------------------------------------------
gdf = gpd.GeoDataFrame.from_postgis(query_dict[objecttype], conn, geom_col='geom')

# ---------------------------------------------
# Export to a shapefile
# ---------------------------------------------
output_path = configapps.OUTPUT_FOLDER_PATH / "pgsql"
output_path.mkdir(exist_ok=True, parents=True)
output_path = output_path / f"pdm_extract_{objecttype}.gpkg"
gdf.to_file(output_path)

print("Shapefile created:", output_path)
