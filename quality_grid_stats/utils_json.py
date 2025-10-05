from pathlib import Path
import json
import config

def json_save(result, country_code, kpitype):
    match kpitype:
        case "osmose":
            folderpath = Path(config.OUTPUT_FOLDER_PATH) / "osmosestats"
            filename = f"{country_code}_osmose_stats.json"
        case "qgstats":
            folderpath = Path(config.OUTPUT_FOLDER_PATH) / "qgstats"
            filename = f"{country_code}_quality_scores_grid_stats.json"
        case _:
            raise AttributeError(f"Unknow KPI type '{kpitype}'")

    folderpath.mkdir(exist_ok=True)
    with open(folderpath / filename, "w",
              encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=4)