import geopandas as gpd

population_grid_file = "../data/kontur_population_20231101_r6_3km.gpkg"

gdf = gpd.read_file(population_grid_file).to_crs(epsg=3857)
gdf["geometry"] = gdf["geometry"].centroid

gdf.to_file("../data/kontur_population_20231101_r6_3km_centroids.gpkg")
