import shutil
from pathlib import Path

import config

source = "../osmwiki/openinframap_countries_info_brut.csv"
destination = Path(config.DATA_FOLDER_PATH) / "00_WORLD" / "openinframap_countries_info_brut.csv"
shutil.copy(source, destination)

source = "../osmwiki/wikidata_countries_info_formatted.csv"
destination = Path(config.DATA_FOLDER_PATH) / "00_WORLD" / "wikidata_countries_info_formatted.csv"
shutil.copy(source, destination)