from pathlib import Path
import geopandas as gpd
import pandas as pd

PROJECT_FOLDER_PATH = Path(__file__).parent.parent

gdf = gpd.read_file("../data/interconnection_final.gpkg")

dfbis = pd.DataFrame(gdf)
del dfbis["geometry"]
dfbis.to_csv("../data/interconnection_final.csv")

gdf = gdf[gdf["power"]!="substation"]

gdf["wikidata"] = gdf["wikidata"].str.split(";")
osm_wd_ids = set()
for w in gdf["wikidata"].tolist():
    for x in w:
        if x:
            osm_wd_ids.add(x)
for w in gdf["wikidata_rel"].tolist():
    if w:
        osm_wd_ids.add(w)



print(osm_wd_ids)

df1 = pd.read_csv(PROJECT_FOLDER_PATH / "data/wikidata/wikidata_electrical_interconnector_full.csv")
df1["source"] = "interconnector"
df2 = pd.read_csv(PROJECT_FOLDER_PATH / "data/wikidata/wikidata_submarine_power_cable_full.csv")
df2["source"] = "submarine_cable"

df = pd.concat([df1, df2])
df["qid"] = df["entity"].str.split("/").apply(lambda x: x[-1])

print(df)
print(df.iloc[34])

wd_wd_ids = set(df["qid"].tolist())

print(wd_wd_ids)

print("--- In wikidata but not in OSM")
for id in wd_wd_ids:
    if id not in osm_wd_ids:
        print(id)

print("--- In OSM but not in Wikidata")
for id in osm_wd_ids:
    if id not in wd_wd_ids:
        print(id)

print("--- In both")
for id in osm_wd_ids:
    if id in wd_wd_ids:
        print(id)


"""set_wikidata = set()

for row in gdf.to_dict(orient='records'):
    row_tag = eval(row["tags"]) if row["tags"] else {}
    row_tag_rel = eval(row["tags_rel"]) if row["tags_rel"] else {}
    if "wikidata" in row_tag:
        set_wikidata.add(row_tag["wikidata"])
    if "wikidata" in row_tag_rel:
        set_wikidata.add(row_tag_rel["wikidata"] + "(rel)")

for el in set_wikidata:
    print(el)

lsttag = gdf["tags"].tolist() + gdf["tags_rel"].tolist()

lsttag = [eval(k) for k in lsttag if k]

keytag = {}


for tg in lsttag:
    if "wikidata" in tg:
        #print(tg)
        set_wikidata.add(tg["wikidata"])
    keytag = {**keytag, **tg}

print(set_wikidata)
print(keytag.keys())"""