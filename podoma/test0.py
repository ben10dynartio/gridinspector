import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent / "common"))

import configapps

import os

import psycopg2
import geopandas as gpd
from shapely import wkb



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

# SQL query: retrieve all non-geometry attributes + WKB geometry
query = """
    SELECT *, ST_AsBinary(geom) AS geom_wkb
    FROM pdm_boundary LIMIT 20;
"""

print("Connected !")
# ---------------------------------------------
# Load data into a GeoDataFrame
# ---------------------------------------------
df = gpd.GeoDataFrame.from_postgis(query, conn, geom_col='geom')

# If the above line fails because of geom type issues, use this fallback:
# (manual WKB decoding)
#
# import pandas as pd
# with conn.cursor() as cur:
#     cur.execute(query)
#     rows = cur.fetchall()
#     colnames = [desc[0] for desc in cur.description]
#
# df = pd.DataFrame(rows, columns=colnames)
# df["geom"] = df["geom_wkb"].apply(lambda x: wkb.loads(x, hex=False))
# gdf = gpd.GeoDataFrame(df, geometry='geom', crs="EPSG:4326")

# ---------------------------------------------
# Export to a shapefile
# ---------------------------------------------
output_path = configapps.OUTPUT_FOLDER_PATH / "pgsql"
output_path.mkdir(exist_ok=True, parents=True)
output_path = output_path / "pdm_boundary.shp"
df.to_file(output_path)

print("Shapefile created:", output_path)
