"""

"""

import argparse
import runpy
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument("action", help="Action")
parser.add_argument("-o", "--outpath", type=str, help="Output data folder path")

args = parser.parse_args()

if args.action == "extractawesomelist": # Quality and Grid Stats
    runpy.run_path(str(Path(__file__).parent / "extract_awesome_list.py"), run_name="__main__")

if args.action == "extractwiki": # Quality and Grid Stats
    runpy.run_path(str(Path(__file__).parent / "extract_wikipage.py"), run_name="__main__")

if args.action == "conflatedatasources": # Quality and Grid Stats
    runpy.run_path(str(Path(__file__).parent / "conflate_sources.py"), run_name="__main__")