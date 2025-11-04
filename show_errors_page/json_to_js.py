import json

with open("gitignore-testfiles/CO_list_errors.json", "r") as f:
    data = json.load(f)

to_js_str = "const errorlist = " + str(data) + ";"

with open("gitignore-testfiles/CO_list_errors.js", "w") as f:
    f.write(to_js_str)