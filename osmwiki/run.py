"""
Use this script for running all steps for one given country
for example, for Colombia (code ISO2 = CO) :
    python run.py osmose CO
    python run.py qgstats CO
"""

import argparse
import runpy
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument("action", help="Action")
parser.add_argument("-o", "--outpath", type=str, help="Output data folder path")

args = parser.parse_args()

"""if args.outpath:
    config.DATA_FOLDER_PATH = Path(args.outpath)"""

if args.action == "openinframap": # Quality and Grid Stats
    runpy.run_path(str(Path(__file__).parent / "openinframap_countries_info.py"), run_name="__main__")

if args.action == "wikidata": # Quality and Grid Stats
    runpy.run_path(str(Path(__file__).parent / "wikidata_countries_info.py"), run_name="__main__")