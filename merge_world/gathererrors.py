import config
import json
import pandas as pd
from pathlib import Path

alldfs = []
for countrycode in config.LIST_COUNTRY_CODES:
    errors = []
    path1 = config.SOURCE_ERRORS_FOLDER_PATH_1 / countrycode
    path2 = config.SOURCE_ERRORS_FOLDER_PATH_2 / countrycode

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

        compile_error_path = config.COMPILE_ERRORS_FOLDER_PATH / countrycode
        compile_error_path.mkdir(exist_ok=True)
        df.to_json(compile_error_path / f"{countrycode}_list_errors.json", orient='records')

        alldfs.append(df)

alldfs = pd.concat(alldfs)
if len(alldfs)>0:
    alldfs.to_json(config.OUTPUT_WORLDWIDE_FOLDER_PATH / "list_osm_errors.json", orient='records')

