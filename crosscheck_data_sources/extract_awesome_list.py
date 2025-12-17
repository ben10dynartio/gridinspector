import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent / "common"))

import configapps

import re

import requests
import pandas as pd

# Warning : These subtitle shall not change
SECTIONS_CONTINENT = ['Africa', 'Asia', 'Australia and New Zealand', 'Europe', 'North America',
                      'South America']

def main():
    download_awesome_list()
    # Charger le fichier
    with open("README.md", "r", encoding="utf-8") as f:
        lines = f.readlines()

    data = []
    title, subtitle = None, None

    # Regex pour détecter liens markdown
    link_pattern = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")

    for line in lines:
        line = line.strip()

        # Détection des titres
        if line.startswith("## "):
            title = line[3:].strip()
            subtitle = None  # reset sous-titre
        elif line.startswith("### "):
            subtitle = line[4:].strip()

        # Détection des bullet points
        elif line.startswith("* "):
            bullet_text = line[2:].strip()

            # Extraire le premier lien (s'il existe)
            match = link_pattern.search(bullet_text)
            link = match.group(2) if match else None

            # Texte sans markdown des liens
            clean_text = link_pattern.sub(r"\1", bullet_text)

            data.append({
                "title": title,
                "subtitle": subtitle,
                "text": clean_text,
                "link_href": link
            })
            #print(data[-1])

    # Construire le tableau
    df = pd.DataFrame(data)
    # print(df["subtitle"].unique().tolist())
    df["continent"] = df["subtitle"]
    del df["subtitle"]
    del df["title"]
    df = df[df["continent"].isin(SECTIONS_CONTINENT)]
    for keyop in ["countryname", "text_refined"]:
        df[keyop] = df["text"].apply(lambda x: extraire_parentheses(x)[keyop])
    df.to_excel("extracted_awesome_list.xlsx")

    df["Country"] = df["countryname"]
    df["Continent"] = df["continent"]
    df["Dataset"] = df["text_refined"]
    df["Link"] = df["link_href"]

    df = df[["Country", "Continent", "Dataset", "Link"]]
    df.to_csv(configapps.OUTPUT_WORLD_FOLDER_PATH / "awesomelist.csv", index=False)


def extraire_parentheses(chaine: str):
    # On cherche un motif qui commence par (quelque chose) suivi du reste
    motif = r'^\(([^)]+)\)\s*(.*)'
    correspondance = re.match(motif, chaine)
    if correspondance:
        return {"countryname":correspondance.group(1), "text_refined":correspondance.group(2)}
    return {"countryname":None, "text_refined": chaine}  # Si pas de parenthèse au début, on retourne None et la chaîne entière


def download_awesome_list():
    url = "https://raw.githubusercontent.com/open-energy-transition/Awesome-Electrical-Grid-Mapping/main/README.md"
    response = requests.get(url)
    if response.ok:
        with open("README.md", "wb") as f:
            f.write(response.content)
        print("Téléchargement réussi.")
    else:
        print("Erreur:", response.status_code)

if __name__ == '__main__':
    main()
