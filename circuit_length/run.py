"""
Use this script for running all steps for one given country
for example, for Colombia (code ISO2 = CO) :
    python run.py circuitlength CO
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent / "common"))

import configapps

import argparse
import runpy
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument("action", help="Action")
parser.add_argument("country", help="Country code iso a2")
parser.add_argument("-i", "--inpath", type=str, help="Input data folder path")
parser.add_argument("-o", "--outpath", type=str, help="Output data folder path")

args = parser.parse_args()

configapps.PROCESS_COUNTRY_LIST = [args.country, ]

if args.outpath:
    configapps.OUTPUT_FOLDER_PATH = Path(args.outpath)
if args.inpath:
    configapps.INPUT_GEODATA_FOLDER_PATH = Path(args.outpath)

if args.action == "circuitlength": # Quality and Grid Stats
    if not args.country:
        raise AttributeError("No country indicated")
    runpy.run_path(str(Path(__file__).parent / "compute_circuit_length.py"), run_name="__main__")

if args.action == "formatcircuitlengthofficial": # Quality and Grid Stats
    runpy.run_path(str(Path(__file__).parent / "format_official_data_length.py"), run_name="__main__")

if args.action == "circuitlengthworldcomparison": # Quality and Grid Stats
    runpy.run_path(str(Path(__file__).parent / "circuit_length_comparison.py"), run_name="__main__")

