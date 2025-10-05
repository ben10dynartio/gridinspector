#!/usr/bin/env python3
"""
Script Python pour :
- découper population.gpkg par shape_country.gpkg (conserver les géométries qui sont dans ou en partie dans le pays)
- récupérer les centroïdes des entités restantes
- créer un raster "carte de chaleur" en utilisant le champ "nombre" (modèle quadratique, rayon 25 km, pixels 500m)
- créer un buffer de 50 km autour des points de substation
- rasteriser le buffer : 0 = proche de substation (dans le buffer), 1 = hors buffer
- multiplier le raster population par le raster substation
- définir 1 si la valeur de chaleur > 10000, sinon 0

Usage:
    python script_geospatial_population_substation.py \
        --country shape_country.gpkg \
        --population population.gpkg \
        --substations substation.gpkg \
        --out_heatmap heatmap.tif \
        --out_proximity proximity.tif \
        --out_combined combined.tif \
        --out_thresholded thresholded.tif

Dépendances : geopandas, rasterio, shapely, numpy, scipy
Installez-les si nécessaire : pip install geopandas rasterio shapely numpy scipy

Remarques :
- Le script reprojette les données en EPSG:3857 (mètres) pour les opérations métriques.
- Pixel size = 500 m (modifiable). Rayon pour le noyau = 25 000 m (25 km).
- Le modèle quadratique utilisé est : w = nombre * (1 - (d/r)^2) pour d <= r, sinon 0.
"""

import argparse
import math
import warnings

import json

from pathlib import Path

import geopandas as gpd
import numpy as np
import rasterio
from rasterio.drivers import raster_driver_extensions
from rasterio.features import shapes
from rasterio.mask import raster_geometry_mask
from rasterio.transform import from_origin
from rasterio.features import rasterize
from shapely.ops import unary_union
from shapely.geometry import mapping
from scipy.spatial import cKDTree
from shapely.geometry import shape

import config

DATA_PATH = config.INPUT_GEODATA_FOLDER_PATH
BUILD_PATH = config.OUTPUT_FOLDER_PATH

def main(country_code):
    country_shape_file = DATA_PATH / f"{country_code}/osm_brut_country_shape.gpkg"
    substation_file = DATA_PATH / f"{country_code}/post_graph_power_nodes_circuit.gpkg"

    clipped_pop_file = BUILD_PATH / f"{country_code}/clip_population.gpkg"
    pop_heatmap_file = BUILD_PATH / f"{country_code}/raster_population_heatmap.tif"
    pop_heatmap_threshold_file = BUILD_PATH / f"{country_code}/raster_population_threshold.tif"
    sub_buffer_file = BUILD_PATH / f"{country_code}/sub_buffer.tif"
    out_coverage_file = BUILD_PATH / f"{country_code}/out_coverage_brut.tif"
    out_coverage_threshold_file = BUILD_PATH / f"{country_code}/out_coverage_threshold.tif"
    missing_coverage_file = BUILD_PATH / f"{country_code}/missing_coverage.gpkg"
    stats_coverage_file = BUILD_PATH / f"{country_code}/{country_code}_spatial_coverage.json"

    pixel_size = 2000.0
    kernel_radius = 15000.0
    substation_coverage_radius = 40000.0
    metric_crs = "EPSG:3857"

    country = gpd.read_file(country_shape_file).to_crs(metric_crs)
    clipped_pop = gpd.read_file(clipped_pop_file)
    try:
        substations = gpd.read_file(substation_file).to_crs(metric_crs)
    except Exception:
        dicstat = {
            "coverage_population": 0.0
        }
        with open(stats_coverage_file, "w", encoding="utf-8") as f:
            json.dump(dicstat, f, ensure_ascii=False, indent=4)
        return

    print(" * Files opened (2)")

    # Définir l'étendue raster à la bbox du country (on peut aussi étendre un peu)
    minx, miny, maxx, maxy = country.total_bounds
    # ajouter marge égale au kernel radius pour capturer influence depuis l'extérieur
    margin = kernel_radius
    bounds = (minx - margin, miny - margin, maxx + margin, maxy + margin)
    transform, width, height, xv, yv = make_raster_grid(bounds, pixel_size)

    raster_population_heatmap = build_heatmap_from_points(clipped_pop, 'population', transform, width, height, xv, yv, kernel_radius)
    raster_population_threshold = (raster_population_heatmap > 10000.0).astype(np.uint8)
    raster_population_threshold = clip_raster_by_country(raster_population_threshold, transform, country, width, height)
    print(" * Heatmap build")
    # rasterize buffer substations
    raster_substation_coverage = rasterize_substation_buffer(substations, pixel_size, bounds, transform, width, height, buffer_distance=substation_coverage_radius)

    # save raster_population_heatmap et raster_substation_coverage
    save_raster(pop_heatmap_file, raster_population_heatmap, transform, metric_crs, dtype=rasterio.float32, nodata=0)
    #save_raster(pop_heatmap_threshold_file, raster_population_threshold, transform, metric_crs, dtype=rasterio.float32, nodata=0)
    save_raster(sub_buffer_file, raster_substation_coverage, transform, metric_crs, dtype=rasterio.uint8, nodata=255)
    print(" * raster_substation_coverage saved")

    # multiplier
    # raster_substation_coverage est 0 pour proche et 1 pour loin — instruction dit : créer raster 0 si proche, 1 sinon
    raster_combined = raster_population_heatmap * raster_substation_coverage.astype(np.float32)
    raster_combined = clip_raster_by_country(raster_combined, transform, country, width, height)
    save_raster(out_coverage_file, raster_combined, transform, metric_crs, dtype=rasterio.float32, nodata=0)
    print(" * raster_combined saved")

    # seuil > 10000 -> 1, else 0
    raster_threshold = (raster_combined > 10000.0).astype(np.uint8)
    raster_threshold = clip_raster_by_country(raster_threshold, transform, country, width, height)
    save_raster(out_coverage_threshold_file, raster_threshold, transform, metric_crs, dtype=rasterio.uint8, nodata=0)
    print(" * raster_threshold saved")

    # vectorisation du raster raster_threshold
    mask = raster_threshold > 0  # True pour les pixels à 1
    features = []
    for geom, val in shapes(raster_threshold, mask=mask, transform=transform):
        features.append({
            "geometry": shape(geom),
            "properties": {"value": int(val)}
        })

    # créer GeoDataFrame
    if features:
        gdf_missing_coverage = gpd.GeoDataFrame.from_features(features, crs=metric_crs)
        print(" Nb of area = ", len(gdf_missing_coverage))
        gdf_missing_coverage["geometry"] = gdf_missing_coverage["geometry"].buffer(-10000)
        gdf_missing_coverage = gdf_missing_coverage[~gdf_missing_coverage["geometry"].is_empty]
        print(" Nb of area after buffering= ", len(gdf_missing_coverage))
        gdf_missing_coverage["geometry"] = gdf_missing_coverage["geometry"].centroid
        # sauvegarder en GeoPackage
        gdf_missing_coverage.to_file(missing_coverage_file, driver="GPKG")

    print("Traitement terminé. Fichiers générés.")
    print("Computation total > pop = ", pall := raster_population_threshold.sum(axis=(0,1)))
    print("Computation non connected > pop = ", pth := raster_threshold.sum(axis=(0,1)))
    dicstat = {
        "coverage_population":float(round((1 - pth/pall)*100,1))
    }
    print(dicstat)
    with open(stats_coverage_file, "w", encoding="utf-8") as f:
        json.dump(dicstat, f, ensure_ascii=False, indent=4)



def compute_centroids(gdf):
    # Assumer gdf en CRS métrique
    cent = gdf.copy()
    cent["centroid"] = cent.geometry.centroid
    cent = cent.set_geometry("centroid")
    return cent


def make_raster_grid(bounds, pixel_size):
    """Retourne transform, width, height et arrays x_centers,y_centers (2D)
    bounds = (minx, miny, maxx, maxy)
    """
    minx, miny, maxx, maxy = bounds
    width = math.ceil((maxx - minx) / pixel_size)
    height = math.ceil((maxy - miny) / pixel_size)
    # ajuster l'origin pour coller aux pixels
    transform = from_origin(minx, maxy, pixel_size, pixel_size)
    # centres des pixels
    xs = minx + (np.arange(width) + 0.5) * pixel_size
    ys = maxy - (np.arange(height) + 0.5) * pixel_size
    xv, yv = np.meshgrid(xs, ys)
    return transform, width, height, xv, yv


def clip_raster_by_country(raster_array, transform, country_gdf, width, height):
    # créer masque rasterisé du pays
    country_union = unary_union(country_gdf.geometry)
    shapes = [(mapping(country_union), 1)]
    mask = rasterize(shapes, out_shape=(height, width), transform=transform, fill=0, dtype=np.uint8)
    return raster_array * mask


def build_heatmap_from_points(centroids_gdf, value_field, transform, width, height, xv, yv, kernel_radius):
    """Construit la heatmap (float32) en utilisant le noyau quadratique pondéré par value_field.
    - centroids_gdf : GeoDataFrame en CRS métrique et géométrie en points
    - xv,yv : matrices 2D des coordonnées des centres de pixels
    """
    # flatten grid centers
    grid_points = np.column_stack((xv.ravel(), yv.ravel()))  # (Ncells, 2)
    tree = cKDTree(grid_points)

    heat = np.zeros(grid_points.shape[0], dtype=np.float64)

    nombres = centroids_gdf[value_field].fillna(0).values
    pts = np.array([[p.x, p.y] for p in centroids_gdf.geometry])

    r = float(kernel_radius)

    for (px, py), nb in zip(pts, nombres):
        if nb == 0:
            continue
        # find grid indices within radius
        idxs = tree.query_ball_point([px, py], r)
        if not idxs:
            continue
        cell_coords = grid_points[idxs]
        dists = np.sqrt((cell_coords[:, 0] - px) ** 2 + (cell_coords[:, 1] - py) ** 2)
        # modèle quadratique : w = nb * (1 - (d/r)^2) pour d <= r
        weights = nb * (1.0 - (dists / r) ** 2)
        # contributions
        heat[idxs] += weights

    heatmap = heat.reshape((height, width))
    return heatmap.astype(np.float32)


def rasterize_substation_buffer(substations_gdf, pixel_size, bounds, transform, width, height, buffer_distance):
    # buffer_distance en mètres (50 km = 50000 m)
    # create buffers in metric CRS
    buffers = substations_gdf.geometry.buffer(buffer_distance)
    # fusionner et dissoudre
    if len(buffers) == 0:
        merged = None
    else:
        merged = unary_union(buffers)
    # rasterize : fill=1 partout sauf brûler 0 pour le buffer
    if merged is None or merged.is_empty:
        # no buffers: all ones
        arr = np.ones((height, width), dtype=np.uint8)
    else:
        shapes = [ (mapping(merged), 0) ]
        arr = rasterize(
            shapes,
            out_shape=(height, width),
            transform=transform,
            fill=1,
            dtype=np.uint8,
        )
    return arr


def save_raster(path, array, transform, crs, dtype=rasterio.float32, nodata=None):
    height, width = array.shape
    with rasterio.open(
        path,
        'w',
        driver='GTiff',
        height=height,
        width=width,
        count=1,
        dtype=dtype,
        crs=crs,
        transform=transform,
        nodata=nodata,
        compress='lzw'
    ) as dst:
        dst.write(array.astype(dtype), 1)


if __name__ == '__main__':
    for country in config.PROCESS_COUNTRY_LIST:
        main(country)
    """for key, val in config.WORLD_COUNTRY_DICT.items():
        print(f"-------- {val} ({key}) -------")
        main(key)"""
