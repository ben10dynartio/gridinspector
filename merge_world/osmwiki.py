import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent / "common"))

import configapps

import shutil
from pathlib import Path

files = ["openinframap_countries_info_brut.csv", "openinframap_countries_info_lua.txt",]
       #  "wikidata_countries_info_formatted.csv", "wikidata_countries_info_brut.csv", "wikidata_countries_info_lua.txt"]

for myfile in files:
    source = Path(__file__).parent.parent / f"osmwiki/{myfile}"
    destination = Path(configapps.OUTPUT_FOLDER_PATH) / "00_WORLD" / myfile
    shutil.copy(source, destination)
