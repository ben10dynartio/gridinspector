import overpass
import shapely.geometry as geometry
from shapely.ops import linemerge, unary_union, polygonize

from ..utils_ovp import overpass_query

#Case study =
# relation/18305461 combinaison of ways
# relation/4635439 two polygons
# relation/13876394 two polygons that are combinaison of ways
overpass_query = ""

api = overpy.Overpass()

query = """ YOUR QUERY HERE """
response = api.query(query)

lss = [] #convert ways to linstrings

for ii_w,way in enumerate(response.ways):
    ls_coords = []

    for node in way.nodes:
        ls_coords.append((node.lon,node.lat)) # create a list of node coordinates

    lss.append(geometry.LineString(ls_coords)) # create a LineString from coords


merged = linemerge([*lss]) # merge LineStrings
borders = unary_union(merged) # linestrings to a MultiLineString
polygons = list(polygonize(borders))