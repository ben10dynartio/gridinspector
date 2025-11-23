import geopandas as gpd

gdf = gpd.read_file("../data/mapyourgrid_team_interconnection.gpkg")

idlist = gdf["id"].astype(str).to_list()

mystr = "way(id:" + ",".join(idlist) + ");"

myg_team = ('Andreas Hernandez', 'ben10dynartio', 'davidtt92', 'map-dynartio', 'Mwiche', 'nlehuby', 'relaxxe', 'Tobias Augspurger', 'InfosReseaux', 'Russ', 'nolann132004')

strmyg = "node(user_touched:" + ",".join([f"\"{n}\"" for n in myg_team]) + ");"
#node(user_touched:"Steve", "jean");
print(mystr)
print(strmyg)