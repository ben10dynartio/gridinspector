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
parser.add_argument("country", help="Country code iso a2")
parser.add_argument("-i", "--inpath", type=str, help="Input data folder path")
parser.add_argument("-o", "--outpath", type=str, help="Output data folder path")

args = parser.parse_args()

config.PROCESS_COUNTRY_LIST = [args.country, ]

if args.outpath:
    config.OUTPUT_FOLDER_PATH = Path(args.outpath)
if args.inpath:
    config.INPUT_GEODATA_FOLDER_PATH = Path(args.outpath)

if args.action == "osmose":
    if not args.country:
        raise AttributeError("No country indicated")
    runpy.run_path("step1_fetch_osmose.py", run_name="__main__")

if args.action == "qgstats": # Quality and Grid Stats
    if not args.country:
        raise AttributeError("No country indicated")
    runpy.run_path("step2_compute_quality_grid_stats.py", run_name="__main__")