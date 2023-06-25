import os, sys
import argparse
import json
from copy import deepcopy

parser = argparse.ArgumentParser(description="Unregister probe data into the appropriate json file.")
parser.add_argument("root", help="Unregister if root matches this.", type=str)
#parser.add_argument("type", help="Type of the case. Must be either 'sim' or 'rec'.", type=str)
parser.add_argument("jsonpath", help="The path to the json files containing the data.")
parser.add_argument("--unregister", help="Whether to actually unregister.", action="store_true", default=False)
args = parser.parse_args()
print(args)

print(f"Using registry {args.jsonpath}")
with open(args.jsonpath) as json_data:
    register = json.load(json_data)

print(f"Loaded registry, containing {len(register['registry'])} items.")
new_register = deepcopy(register)
new_register["registry"] = []

for item in register["registry"]:
    if args.root == item["root"]:
        print(f"Would remove {item}.")
    else:
        new_register["registry"].append(item)

if args.unregister:
    with open(args.jsonpath, "w") as json_data:
        json.dump(new_register, json_data, indent=4, sort_keys=True)
    print(f"Wrote new register, containing {len(new_register['registry'])} items.")

print("ALLDONE.")
