"""
Use this script for running all steps for one given country
for example, for Colombia (code ISO2 = CO) :
    python run.py osmose CO
    python run.py qgstats CO
"""

import argparse
import config
import runpy
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument("action", help="Action")
parser.add_argument("-o", "--outpath", type=str, help="Output data folder path")

args = parser.parse_args()

config.PROCESS_COUNTRY_LIST = [args.country, ]

if args.outpath:
    config.DATA_FOLDER_PATH = Path(args.outpath)

if args.action == "qgstats": # Quality and Grid Stats
    runpy.run_path("qgstats.py", run_name="__main__")

if args.action == "osmwiki": # Quality and Grid Stats
    runpy.run_path("osmwiki.py", run_name="__main__")