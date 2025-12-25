"""
This script generate country pages for #MapYourGrid website
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent / "common"))

import configapps

import os
import zipfile
import pandas as pd
from pathlib import Path


COUNTRY_PAGE_TEMPLATE = Path(__file__).parent / "countrypages_template.md"

DESTINATION_DIRECTORY = configapps.OUTPUT_FOLDER_PATH / "countrypages"
DESTINATION_DIRECTORY.mkdir(exist_ok=True)
#MAPS_IMAGES_DIRECTORY = configapps.OUTPUT_FOLDER_PATH / "images/maps_countries"


def main(country_code):
    df_wikidata = pd.read_csv(configapps.OUTPUT_FOLDER_PATH / "00_WORLD/wikidata_countries_info_formatted.csv", na_filter=False).set_index("codeiso2")
    # wikidata_dict = {row["codeiso2"]: row for row in df_wikidata.to_dict(orient='records')}

    df_openinframap = pd.read_csv(configapps.OUTPUT_FOLDER_PATH / "00_WORLD/openinframap_countries_info_brut.csv", na_filter=False).set_index("codeiso2")
    # openinframap_dict = {row["codeiso2"]: row for row in df.to_dict(orient='records')}

    df_powergrid = pd.read_csv(configapps.OUTPUT_FOLDER_PATH / "00_WORLD/worldwide_quality_grid_stats.csv", na_filter=False).set_index("codeiso2")
    # powergrid_dict = {row["codeiso2"]: row for row in df.to_dict(orient='records')}

    """ Following lines extract the country list per continent. You can use one of the following dict as a country list"""
    """extract_dict = {idx: df_wikidata.loc[idx].get("name")
                    for idx in df_wikidata.index if df_wikidata.loc[idx].get("continent") == "Oceania"}

    extract_dict = {idx: df_wikidata.loc[idx].get("name")
                    for idx in df_wikidata.index if df_wikidata.loc[idx].get("continent") == "North America"}

    extract_dict = {idx: df_wikidata.loc[idx].get("name")
                    for idx in df_wikidata.index if df_wikidata.loc[idx].get("continent") == "Europe"}

    COUNTRY_LIST = {idx: df_wikidata.loc[idx].get("name") for idx in df_wikidata.index}
    SKIP_UNTIL = None  # not in use yet"""


    # The following section are conditional, only for countries with map
    SECTION_PROGRESS_MAP = """
        ## Progress map

        <center>
        <img src="https://raw.githubusercontent.com/ben10dynartio/mapyourgrid-website-files/refs/heads/main/docs/images/maps_countries/{{COUNTRY_CODE}}/high-voltage-network.jpg" width="60%">
        <img src="../../images/maps_countries_legend_progress.jpg" width="50%">
        </center>
        """.replace("        ", "")

    SECTION_GRID_CONNECTIVITY = """
        ## Grid connectivity overview

        Grid structure (nb of substations x nb of connections) : {{POWER_GRID_CONNECTIVITY}}

        <center>
        <img src="https://raw.githubusercontent.com/ben10dynartio/ohmygrid-website-files/refs/heads/main/docs/images/maps_countries/{{COUNTRY_CODE}}/grid-connectivity.jpg" width="60%">
        <img src="../../images/maps_countries_legend_grid.jpg" width="50%">
        </center>
        """.replace("        ", "")

    ## Building MD file &

    df_collector = []  # To collect each country informations

    template_data = {}
    template_data["COUNTRY_CODE"] = country_code

    template_data["COUNTRY_NAME"] = df_wikidata.loc[country_code]["countryLabel"]
    template_data["COUNTRY_CONTINENT"] = df_wikidata.loc[country_code]["continent"]
    template_data["COUNTRY_POPULATION"] = df_wikidata.loc[country_code]["population"]
    template_data["COUNTRY_AREA"] = df_wikidata.loc[country_code]["area_km2"]
    template_data["COUNTRY_GDP"] = df_wikidata.loc[country_code]["gdp_bd"]
    template_data["COUNTRY_OSM_REL_ID"] = df_wikidata.loc[country_code]["osm_rel_id"]
    template_data["COUNTRY_WIKIDATA_ID"] = df_wikidata.loc[country_code]["osm_rel_id"]
    template_data["COUNTRY_FLAG_IMAGE"] = df_wikidata.loc[country_code]["flag_image_url"]
    template_data["COUNTRY_MAP_IMAGE"] = df_wikidata.loc[country_code]["locator_map_url"]

    if country_code in df_openinframap.index:
        template_data["POWER_LINES_KM"] = df_openinframap.loc[country_code]["power_line_total_length"]
        template_data["POWER_PLANTS_MW"] = df_openinframap.loc[country_code]["power_plant_output_mw"]
        template_data["POWER_PLANTS_NB"] = int(df_openinframap.loc[country_code]["power_plant_count"])

    template_data["POWER_SUBSTATIONS_NB"] = ''
    template_data["POWER_INTERCONNECTIONS_NB"] = ''
    template_data["POWER_GRID_CONNECTIVITY"] = ''
    if country_code in df_powergrid.index:
        if df_powergrid.loc[country_code].get("nb_substations"):
            template_data["POWER_SUBSTATIONS_NB"] = int(float(df_powergrid.loc[country_code]["nb_substations"]))
            template_data["POWER_INTERCONNECTIONS_NB"] = int(
                float(df_powergrid.loc[country_code]["nb_international_connections"]))
        template_data["POWER_GRID_CONNECTIVITY"] = df_powergrid.loc[country_code]["grid_structure"]

    template_data["SECTION_GRID_CONNECTIVITY"] = ""
    template_data["SECTION_PROGRESS_MAP"] = ""
    #if Path(MAPS_IMAGES_DIRECTORY / f"{country_key}/high-voltage-network.jpg").is_file():
    template_data["SECTION_GRID_CONNECTIVITY"] = SECTION_GRID_CONNECTIVITY
    template_data["SECTION_PROGRESS_MAP"] = SECTION_PROGRESS_MAP

    # Open COUNTRY_PAGE_TEMPLATE and replace "{{ }}" string with corresponding value
    # It is done twice to manage SECTION_* values that are designed above
    with open(COUNTRY_PAGE_TEMPLATE, 'r', encoding='utf-8') as f:
        contenu = f.read()
        for key, val in template_data.items():
            contenu = contenu.replace(f'{{{{{key}}}}}', str(val))
        for key, val in template_data.items():
            contenu = contenu.replace(f'{{{{{key}}}}}', str(val))

    # Export all md files for countries
    Path.mkdir(DESTINATION_DIRECTORY, exist_ok=True)
    with open(DESTINATION_DIRECTORY / f"{template_data['COUNTRY_NAME']}.md", 'w', encoding='utf-8') as f:
        #print("+", end="")
        f.write(contenu)

    df_collector.append(template_data)

    # Construct the string for the list of country (to be insterted on "progress.md" pages)
    """df_collector = pd.DataFrame(df_collector)
    lst_continent = df_collector['COUNTRY_CONTINENT'].unique().tolist()
    lst_continent.sort()
    mystr = ""
    for continent in lst_continent:
        # print("###", continent, "\n")
        mystr += "###" + continent + "\n"
        dft = df_collector[df_collector['COUNTRY_CONTINENT'] == continent]
        for r in dft.to_dict(orient='records'):
            # Country name link to the page, with a small flag on the left
            mystr += (f"![Flag {r['COUNTRY_NAME']}]({r['COUNTRY_FLAG_IMAGE']}){{width=20px}} "
                      f"[{r['COUNTRY_NAME']}](countrypages/{r['COUNTRY_NAME']}.md) - \n")
            # print(mystr, end="")
        mystr += "\n"
        # print("\n")"""

    """r = requests.get(
        'https://raw.githubusercontent.com/open-energy-transition/Oh-my-Grid/refs/heads/main/docs/progress.md')
    newfile = r.text.replace("<!-- COUNTRY_LIST_INSERTION -->", mystr)
    with open(PROGRESS_PAGE_PATH, 'w') as f:
        f.write(newfile)"""

    """with open(COUNTRY_LIST_PATH, 'w') as f:
        f.write(mystr)"""


    #zip_folder(MAPS_IMAGES_DIRECTORY)


def zip_folder(folder_path, output_path=None):
    if not os.path.isdir(folder_path):
        raise ValueError(f"This folder does not exist : {folder_path}")

    if output_path is None:
        output_path = Path(__file__).parent.parent.parent / ("zips/" + folder_path.name + ".zip")

    with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(folder_path):
            for file in files:
                abs_path = os.path.join(root, file)
                rel_path = "docs/" + os.path.relpath(abs_path, folder_path)
                zipf.write(abs_path, arcname=rel_path)

    #print(f" -- Country pages zip done : {output_path}")


if __name__ == '__main__':
    for country in list(configapps.WORLD_COUNTRY_DICT.keys()):
        main(country)
    zip_folder(DESTINATION_DIRECTORY, output_path=configapps.OUTPUT_FOLDER_PATH / "00_WORLD/countrypages.zip")