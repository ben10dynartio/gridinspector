"""
This script requests OpenInfraMap API on certains properties. The collected data are structured
to feed the following OpenStreetMap Wiki Page : https://wiki.openstreetmap.org/wiki/Module:OpeninframapCountryInfo
These data can thus be used largely in the wiki.

Update of data requires to run this script and updating wiki module page with the script's output (console or txt file).

Script by ben10dynartio under WTFPL Licence where not covered by the dependancy licences.
"""

import requests
import pandas as pd
import numpy as np
from urllib.parse import unquote
from datetime import datetime
from pathlib import Path

####### SCRIPT CONFIGURATION ##################################################
# URL de l'endpoint OpenInfraMap
ENDPOINT_URL = "https://openinframap.org/stats/country/"

# list of iso code of countries
countrylist = ["AF", "AL", "DZ", "AD", "AO", "AG", "AR", "AM", "AU", "AT", "AZ", "BH", "BD", "BB", "BY", "BE", "BZ",
               "BJ", "BT", "BO", "BA", "BW", "BR", "BN", "BG", "BF", "BI", "KH", "CM", "CA", "CV", "CF", "TD", "CL",
               "CO", "KM", "CR", "HR", "CU", "CY", "CZ", "CD", "DK", "DJ", "DM", "DO", "EC", "EG", "SV", "GQ", "ER",
               "EE", "SZ", "ET", "FM", "FJ", "FI", "FR", "GA", "GE", "DE", "GH", "GR", "GD", "GT", "GN", "GW", "GY",
               "HT", "HN", "HU", "IS", "IN", "ID", "IR", "IQ", "IE", "IL", "IT", "CI", "JM", "JP", "JO", "KZ", "KE",
               "NL", "KI", "KW", "KG", "LA", "LV", "LB", "LS", "LR", "LY", "LI", "LT", "LU", "MG", "MW", "MY", "MV",
               "ML", "MT", "MH", "MR", "MU", "MX", "MD", "MC", "MN", "ME", "MA", "MZ", "MM", "NA", "NR", "NP", "NZ",
               "NI", "NE", "NG", "KP", "MK", "NO", "OM", "PK", "PW", "PA", "PG", "PY", "CN", "PE", "PH", "PL", "PT",
               "QA", "CG", "RO", "RU", "RW", "KN", "LC", "VC", "WS", "SM", "SA", "SN", "RS", "SC", "SL", "SG", "SK",
               "SI", "SB", "SO", "ZA", "KR", "SS", "ES", "LK", "PS", "SD", "SR", "SE", "CH", "SY", "ST", "TW", "TJ",
               "TZ", "TH", "BS", "GM", "TL", "TG", "TO", "TT", "TN", "TR", "TM", "TV", "UG", "UA", "AE", "GB", "US",
               "UY", "UZ", "VU", "VA", "VE", "VN", "YE", "ZM", "ZW"]

EXPORT_FOLDER_PATH = Path(__file__).parent.parent / "data_out/00_WORLD" # Change it if you don't like
EXPORT_FOLDER_PATH.mkdir(parents=True, exist_ok=True)

PATH_BRUT_DATA = EXPORT_FOLDER_PATH / "openinframap_countries_info_brut.csv"
#PATH_FORMAT_DATA = EXPORT_FOLDER_PATH / "openinframap_countries_info_formatted.csv"
PATH_LUA_DATA = EXPORT_FOLDER_PATH / "openinframap_countries_info_lua.txt"

####### FUNCTION DEFINITION ###################################################
def fetch_endpoint(countrycode):
    """ Fetch OpenInfraMap on a country """
    url = ENDPOINT_URL + countrycode + ".json"
    response = requests.get(url)
    response.raise_for_status()
    return response.json()


def build_voltage_range_dict():
    """ Build a dict from API with user interface text
    Example : {(0, 10000): '< 10 kV', (10000, 25000): '10 kV - 25 kV', ...
    """
    myjsonlines = fetch_endpoint(countrylist[0])["lines"]
    voltage_range_dict = {}
    for p in myjsonlines:
        if p["min_voltage"] and p["max_voltage"]:
            range_string = f'{int(p["min_voltage"]/1000)} kV - {int(p["max_voltage"]/1000)} kV'
        elif p["min_voltage"]:
            range_string = f'> {int(p["min_voltage"] / 1000)} kV'
        elif p["max_voltage"]:
            range_string = f'< {int(p["max_voltage"] / 1000)} kV'
        else:
            range_string = "No voltage tagged"
        voltage_range_dict[(p["min_voltage"], p["max_voltage"])] = range_string
    return voltage_range_dict


def build_country_power_line_length_list(jsondata, voltage_range_dict):
    mylines = jsondata["lines"]
    my_country_power_line_length_dict = {(p["min_voltage"], p["max_voltage"]) : f'{int(p["length"]/1000):,}'
                                         for p in mylines}
    my_country_power_line_length_list = ['"' + str(my_country_power_line_length_dict[key]) + '"'
                                         for key in voltage_range_dict.keys()]
    return my_country_power_line_length_list


def build_country_power_line_total_length(jsondata):
    line_sum = sum([p["length"] for p in jsondata["lines"]])
    return int(line_sum/1000)


def get_country_power_plant_count(jsondata):
    return jsondata["plant_stats"]['count']


def get_country_power_plant_output_mw(jsondata):
    return int(jsondata["plant_stats"]['output']/1000000)


def format_as_lua_data(result_dict, voltage_range_dict):
    """ Tranform result_dict and voltage_range_dict in a Lua format to copy-paste on a Lua-wiki-module

    Return:
        string: lua-formatted string
    """
    mystr = "-- begin data section\n"

    voltage_range_order = ", ".join([f'\"{p}\"' for i, p in enumerate(list(voltage_range_dict.values()))])
    mystr += "power_line_voltage_range = {" + voltage_range_order + "}\n\n"

    mystr += "power_line_range_length_km = {"
    for key, dic in result_dict.items():
        addstr = ", ".join([f'{p}' for i, p in enumerate(dic["power_line_range_length"])])
        mystr += f'{key} = ' + '{' + addstr + '}, '
    mystr += "}\n\n"

    mystr += "power_line_total_length_km = {"
    mystr += ", ".join([f'{key} = \"{int(dic["power_line_total_length"]):,}\"' for key, dic in result_dict.items()])
    mystr += "}\n\n"

    mystr += "power_plant_count = {"
    mystr += ", ".join([f'{key} = \"{str(dic["power_plant_count"])}\"' for key, dic in result_dict.items()])
    mystr += "}\n\n"

    mystr += "power_plant_output_mw = {"
    mystr += ", ".join([f'{key} = \"{int(dic["power_plant_output_mw"]):,}\"' for key, dic in result_dict.items()])
    mystr += "}\n\n"

    mystr += f'last_update = \"{datetime.today().strftime("%Y-%m-%d")}\"'
    mystr += "\n-- end data section"

    return mystr


####### MAIN SCRIPT ###########################################################
if __name__ == '__main__':
    voltage_range_dict = build_voltage_range_dict()
    result_dict = {}
    df_data = []
    print(">> Requesting countries")
    for i, countrycode in enumerate(countrylist):
        print(countrycode, " ", end="")
        result_dict[countrycode] = {}
        jsonresult = fetch_endpoint(countrycode)
        result_dict[countrycode]["json"] = jsonresult
        result_dict[countrycode]["power_line_range_length"] = (
            build_country_power_line_length_list(jsonresult, voltage_range_dict))
        result_dict[countrycode]["power_line_total_length"] = (
            build_country_power_line_total_length(jsonresult))
        result_dict[countrycode]["power_plant_count"] = get_country_power_plant_count(jsonresult)
        result_dict[countrycode]["power_plant_output_mw"] = get_country_power_plant_output_mw(jsonresult)
        df_data.append({"codeiso2":countrycode, **{key:val for key, val in result_dict[countrycode].items() if key != "json"}})
        if (i+1)%25 == 0:
            print()

    # Build csv file
    df = pd.DataFrame(df_data)
    df.to_csv(PATH_BRUT_DATA, index=False)

    # Build Lua Structure for wiki module and export it
    wikistring = format_as_lua_data(result_dict, voltage_range_dict)
    with open(PATH_LUA_DATA, "w") as text_file:
        text_file.write(wikistring)
    print("\n\n", wikistring)
