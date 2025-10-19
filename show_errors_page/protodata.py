import json
import random

with open("list_osm_errors.json", "r") as file:
    myjson = json.load(file)

print(f"There are {len(myjson)} errors in the world")

tablelight = []

for i in range(100):
    x = random.randint(0, len(myjson)-1)
    tablelight.append(myjson[x])

# Conversion en JSON (équivalent JavaScript)
js_equivalent = json.dumps(tablelight, indent=4)

# Affichage sous forme de structure JS
print("const monObjet = ")
print(js_equivalent + ";")
