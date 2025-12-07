import configapps
import json
from pathlib import Path
import time

class Timer(object):
    def __init__(self, name=None):
        self.name = name

    def __enter__(self):
        self.tstart = time.time()

    def __exit__(self, type, value, traceback):
        if self.name:
            print('[%s]' % self.name,)
        print('Elapsed: %s' % (time.time() - self.tstart))


def add_error(errorlist, errordict, log_level=configapps.LOG_LEVEL):
    if log_level == "DEBUG":
        print("  * ERROR :", errordict)
    errorlist.append(errordict)


def errors_to_file(data, country_code, filename):
    Path(configapps.ERRORS_FOLDER_PATH).mkdir(exist_ok=True)
    Path(configapps.ERRORS_FOLDER_PATH / country_code).mkdir(exist_ok=True)
    with open(configapps.ERRORS_FOLDER_PATH / country_code / filename, "w", encoding="utf-8") as f:
        json.dump(data, f)


def json_to_js(source_filename, destination_filename, js_var_name):
    with open(source_filename, "r") as f:
        data = json.load(f)

    to_js_str = "const " + js_var_name + " = " + str(data) + ";"

    to_js_str = to_js_str.replace("None", "null")

    with open(destination_filename, "w") as f:
        f.write(to_js_str)

