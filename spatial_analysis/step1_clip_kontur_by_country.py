import warnings
from pathlib import Path

import geopandas as gpd

from shapely.ops import unary_union


import config

COUNTRY_CODE = config.COUNTRY_CODE
kernel_radius = 25000.0
metric_crs = "EPSG:3857"

data_path = config.INPUT_GEODATA_FOLDER_PATH

population_grid_file = f"data_kontur/kontur_population_20231101_r6_3km_centroids.gpkg"
gdf_population = gpd.read_file(population_grid_file).to_crs(metric_crs)

def clip_population_by_country(pop_gdf, country_union, crs):
    # Intersecter pour garder uniquement les parties à l'intérieur du pays (ou en partie)
    # On suppose qu'il y a au moins une géométrie pays ; si plusieurs, on les unionne

    country_single = gpd.GeoDataFrame(geometry=[country_union], crs=crs)
    clipped = pop_gdf.sjoin(country_single, how="inner")
    return clipped

def main(country_code):
    output_data_folder = Path(config.OUTPUT_FOLDER_PATH / {country_code})

    # Open files
    country_shape_file = data_path / f"{country_code}/osm_brut_country_shape.gpkg"
    country = gpd.read_file(country_shape_file).to_crs(metric_crs)
    country_union = unary_union(country.geometry).buffer(kernel_radius + 10000)

    print(" * Files opened")

    if 'population' not in gdf_population.columns:
        raise KeyError("La couche population doit contenir le champ 'population'.")
    print(" * Reprojected layers")

    # découpage
    clipped_pop = clip_population_by_country(gdf_population, country_union, metric_crs)
    if clipped_pop.empty:
        warnings.warn("Aucune entité population après découpage par le pays.")

    print("Population clipped")

    output_data_folder.mkdir(exist_ok = True)
    clipped_pop.to_file(output_data_folder / f"clip_population.gpkg")

if __name__ == "__main__":
    for country in config.PROCESS_COUNTRY_LIST:
        main(country)

    #for key, val in config.WORLD_COUNTRY_DICT.items():
    #    main(key)