import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent / "common"))

import configapps

from utils_exec import json_to_js

import json
import pandas as pd
from pathlib import Path

alldfs = []
for countrycode in configapps.LIST_COUNTRY_CODES:
    errors = []
    path1 = configapps.ERRORS_FOLDER_PATH / countrycode
    path2 = configapps.ERRORS_FOLDER_PATH2 / countrycode

    if path1.is_dir():
        for element in path1.iterdir():
            if element.is_file():
                if element.name.endswith(".json"):
                    with open(element, "r") as jsonfile:
                        errors.extend(json.load(jsonfile))

    if path2.is_dir():
        for element in path2.iterdir():
            if element.is_file():
                if element.name.endswith(".json"):
                    with open(element, "r") as jsonfile:
                        errors.extend(json.load(jsonfile))

    if len(errors)>0:
        df = pd.DataFrame(errors)
        df.insert(0, "country_code_iso2", countrycode)

        compile_error_path = configapps.COMPILE_ERRORS_FOLDER_PATH / countrycode
        compile_error_path.mkdir(exist_ok=True)
        json_filename = compile_error_path / f"{countrycode}_list_errors.json"
        js_filename = compile_error_path / f"{countrycode}_list_errors.js"
        df.to_json(json_filename, orient='records')

        json_to_js(json_filename, js_filename, "list_osm_errors")

        alldfs.append(df)

alldfs = pd.concat(alldfs)
if len(alldfs)>0:
    alldfs.to_json(configapps.OUTPUT_WORLD_FOLDER_PATH / "list_osm_errors.json", orient='records')

