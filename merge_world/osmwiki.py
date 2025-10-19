import shutil
from pathlib import Path

import config

files = ["openinframap_countries_info_brut.csv", "openinframap_countries_info_lua.txt",
         "wikidata_countries_info_formatted.csv", "wikidata_countries_info_lua.txt"]

for myfile in files:
    source = Path(__file__).parent.parent / f"osmwiki/{myfile}"
    destination = Path(config.DATA_FOLDER_PATH) / "00_WORLD" / myfile
    shutil.copy(source, destination)

"""source = Path(__file__).parent.parent / "osmwiki/openinframap_countries_info_brut.csv"
destination = Path(config.DATA_FOLDER_PATH) / "00_WORLD" / "openinframap_countries_info_brut.csv"
shutil.copy(source, destination)

source = Path(__file__).parent.parent / "osmwiki/wikidata_countries_info_formatted.csv"
destination = Path(config.DATA_FOLDER_PATH) / "00_WORLD" / "wikidata_countries_info_formatted.csv"
shutil.copy(source, destination)"""