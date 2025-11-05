# MapYourGrid Apps

These apps are used to process data about transmission power line in OpenStreetMap around the world. 

It contains the following tools :
- `circuit_length` : compute the length of power line and circuits
- `crosscheck_data_source` : Fetch sources from OSM Wiki and from awesome list and compare them
- `gridgraph_webpage` : prototyping
- `indicators_map` : file used to rendeer the global map, see : https://apps.dynartio.com/mapyourgrid/indicatormap.html
- `merge_world` : used to merge all tools output and produce the indicator map
- `ohsome_power_lines_length` : fetch Ohsome to get historical power line length data
- `osmwiki` : tool to fetch data from Wikidata and OpenInfraMap
- `quality_grid_stats` : perform grid and connectivity analysis 
- `show_errors_page` : in developpement (rendeer collected errors during script execution)
- `spatial_analysis` : evaluate the coverage of substation based on population density
- `voltage_operator_analysis` : extract data about voltages and operator for each country


# OSM Grid Health Score
This repository is used to build the health score map.


## Line/circuit length calculation details
The line length calculation comes initially from an overpass script which fetches all lines (and metadata) of a country. 
### Important details
1)  This does not include lines "under construction" for the moment.
2)  This takes the entire "way" of power lines, which means that interconnector line lengths can be overestimated if mapped well into another country. This can explain certain countries having a score well-above 100% for a specific voltage.
3)  Circuit tags are crucial for a valid comparison of actual line mapping coverage. Certain countries can have all lines fully mapped, but may lack circuit tags which can underestimate the actual coverage of lines mapped.
4)  If circuit tags are missing then circuit = 1
5) When comparing official data and OSM extracted data of circuit lengths, check the certainty of the official source to see if it's circuits or lines on the wiki page.
