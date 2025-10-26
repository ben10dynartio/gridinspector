import config
import json
import runpy
from pathlib import Path


def add_error(errorlist, errordict, log_level=config.LOG_LEVEL):
    if log_level == "DEBUG":
        print("  * ERROR :", errordict)
    errorlist.append(errordict)

def errors_to_file(data, country_code, filename):
    Path(config.ERRORS_PATH).mkdir(exist_ok=True)
    Path(config.ERRORS_PATH / country_code).mkdir(exist_ok=True)
    with open(config.ERRORS_PATH / country_code / filename, "w", encoding="utf-8") as f:
        json.dump(data, f)