"""
Use this script for running all steps for one given country
for example, for Colombia (code ISO2 = CO) :
    python run.py osmose CO
    python run.py qgstats CO
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent / "common"))

import configapps

import argparse
import config
import runpy
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument("action", help="Action")
parser.add_argument("-o", "--outpath", type=str, help="Output data folder path")

args = parser.parse_args()

if args.outpath:
    configapps.DATA_FOLDER_PATH = Path(args.outpath)

if args.action == "qgstats": # Quality and Grid Stats
    runpy.run_path(str(Path(__file__).parent / "qgstats.py"), run_name="__main__")

if args.action == "osmwiki": # Quality and Grid Stats
    runpy.run_path(str(Path(__file__).parent / "osmwiki.py"), run_name="__main__")

if args.action == "spatialanalysis": # Quality and Grid Stats
    runpy.run_path(str(Path(__file__).parent / "spatialanalysis.py"), run_name="__main__")

if args.action == "voltageoperator": # Quality and Grid Stats
    runpy.run_path(str(Path(__file__).parent / "voltageoperator.py"), run_name="__main__")

if args.action == "buildworldmap": # Quality and Grid Stats
    runpy.run_path(str(Path(__file__).parent / "buildworldmap.py"), run_name="__main__")

if args.action == "gathererrors": # Quality and Grid Stats
    runpy.run_path(str(Path(__file__).parent / "gathererrors.py"), run_name="__main__")

if args.action == "circuitlength": # Quality and Grid Stats
    runpy.run_path(str(Path(__file__).parent / "circuitlength.py"), run_name="__main__")

if args.action == "countrypages": # Quality and Grid Stats
    runpy.run_path(str(Path(__file__).parent / "countrypages.py"), run_name="__main__")