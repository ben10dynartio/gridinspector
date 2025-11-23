import requests
import osm2geojson
import geopandas

from utils_ovp import overpass_query

# Config
PATH_OVERPASSED_COUNTRIES = "data/overpassed_countrylist/" # Contains the results of Overpass requests for each country
PATH_CONCAT_OVERPASSED_COUNTRIES = "data/osm_crossing_border_power_lines.gpkg"
PATH_OVERPASSED_WAYS = "data/overpassed_ways/" # Contains the results of Overpass requests for each found way
PATH_REFINED_WAYS = "data/refined_osm_crossing_border_power_lines.gpkg"

# List of queried country ISO 3166-1 alpha-2 codes
countrylist = ["AF", "AL", "DZ", "AD", "AO", "AG", "AR", "AM", "AU", "AT", "AZ", "BH", "BD", "BB", "BY", "BE", "BZ",
               "BJ", "BT", "BO", "BA", "BW", "BR", "BN", "BG", "BF", "BI", "KH", "CM", "CA", "CV", "CF", "TD", "CL",
               "CO", "KM", "CR", "HR", "CU", "CY", "CZ", "CD", "DJ", "DK", "DM", "DO", "EC", "EG", "SV", "GQ", "ER", "EE",
               "SZ", "ET", "FM", "FJ", "FI", "FR", "GA", "GE", "DE", "GH", "GR", "GD", "GT", "GN", "GW", "GY", "HT",
               "HN", "HU", "IS", "IN", "ID", "IR", "IQ", "IE", "IL", "IT", "CI", "JM", "JP", "JO", "KZ", "KE", "NL",
               "KI", "KW", "KG", "LA", "LV", "LB", "LS", "LR", "LY", "LI", "LT", "LU", "MG", "MW", "MY", "MV", "ML",
               "MT", "MH", "MR", "MU", "MX", "MD", "MC", "MN", "ME", "MA", "MZ", "MM", "NA", "NR", "NP", "NZ", "NI",
               "NE", "NG", "KP", "MK", "NO", "OM", "PK", "PW", "PA", "PG", "PY", "CN", "PE", "PH", "PL", "PT", "QA",
               "CG", "RO", "RU", "RW", "KN", "LC", "VC", "WS", "SM", "SA", "SN", "RS", "SC", "SL", "SG", "SK", "SI",
               "SB", "SO", "ZA", "KR", "SS", "ES", "LK", "PS", "SD", "SR", "SE", "CH", "SY", "ST", "TW", "TJ", "TZ",
               "TH", "BS", "GM", "TL", "TG", "TO", "TT", "TN", "TR", "TM", "TV", "UG", "UA", "AE", "GB", "US", "UY",
               "UZ", "VU", "VA", "VE", "VN", "YE", "ZM", "ZW"]


def query_by_ids(type, ids) -> str:
    """ Query to get objects by ids """
    str_ids = ','.join([str(i) for i in ids if i])
    query = f"""
    [out:json][timeout:350];
    {type}(id:{str_ids});
    out meta geom;
    """
    return query


def overpass_response_to_gdf(response, tags=[]):
    geojson = osm2geojson.json2geojson(response, log_level="DEBUG")

    if len(geojson["features"])>0:
        gdf = geopandas.GeoDataFrame.from_features(geojson, crs=4326)
        gdf["object_type"] = gdf["type"]
        del gdf["type"]
        gdf["osmid"] = gdf["object_type"] + "/" + gdf["id"].astype(str)
        for tag in tags:
            gdf[tag] = gdf["tags"].apply(lambda x: x.get(tag) if type(x) is dict else "")
    else:
        gdf = geopandas.GeoDataFrame(columns=["object_type", "id", "tags", "osmid", "geometry"] + tags, geometry='geometry', crs=4326)
    return gdf

