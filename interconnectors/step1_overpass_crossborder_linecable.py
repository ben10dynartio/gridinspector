"""
This script request all lines that are crossing a admin_level=2 border
"""
from common import overpass_query, overpass_response_to_gdf

query = """
    [out:json][timeout:2000]; 
    area["ISO3166-1:alpha2"][admin_level=2];
    //area["ISO3166-1:alpha2"~"^(TZ|KE)$"][admin_level=2];

    for (t["ISO3166-1:alpha2"]) {
        ._->.searchArea;
        (way["power"="line"] (area.searchArea);way["power"="cable"] (area.searchArea);)->.power_ways;
        node(w.power_ways:1,-1)->.total_line_end;	
        node.total_line_end(area.searchArea)->.total_inside_country;	
        (node.total_line_end;-node.total_inside_country;)->.foreign_ends;
        foreach.foreign_ends (
            (way(bn).power_ways;.lineset;)->.lineset;
        );
      (.allset;.lineset;)->.allset; 
    }
    .allset;
    out meta geom;
    """

# be patient, may last 20 min ...
response = overpass_query(query)
overpass_response_to_gdf(response).to_file("osm_crossborder_linecable_brut.gpkg")