import os, sys
import argparse
import json

parser = argparse.ArgumentParser(description="Register probe data into the appropriate json file. ")


parser.add_argument("name", help="Name of the case.", type=str)
parser.add_argument("type", help="Type of the case. Must either end in 'json', or be either 'sim' or 'rec'.", type=str)
parser.add_argument("dest", help="Destination folder below the 'root' directory in the registry to store the probe files.", type=str)
parser.add_argument("fs", help="Sample rate in Hz.", type=float)
parser.add_argument("dims", help="The dims expressed as an array, e.g. '[1.2, 0.5]'.", type=str)
parser.add_argument("plume_source", help="Source location expressed as an array, e.g. '[0.2, 0.250]'.", type=str)
parser.add_argument("fields", help="List of fields, comma separated, e.g. 'S1,S2'.")
parser.add_argument("--source", help="Source folder containing the probe files. Defaults to the folder with the name given.", type=str, default="")
parser.add_argument("--colour", help="The colour to use.", type=str, default="violet")
parser.add_argument("--jsonpath", help="The path to the json files containing the data.", type=str, default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "plumes"))
parser.add_argument("--overwrite", help="Whether to overwrite an item if it already exists.", action="store_true", default=False)
parser.add_argument("--nocopy", action="store_true", help="If set, doesn't actually copy the probe files over. Useful if they've been moved manually.")
parser.add_argument("--mock", action="store_true", help="If set, doesn't actually write the new registry.")
args = parser.parse_args()
print(args)

if args.type not in ["sim", "rec"]:
    if not args.type.endswith("json"):
        raise ValueError("type must be 'sim' or 'rec', or be the name of a json file.")

file_name = args.type if args.type.endswith("json") else {"sim": "simulations.json", "rec":"recordings.json"}
reg_file  = os.path.join(args.jsonpath, file_name)

# Registry is formed as args.jsonpath/[simulations.json|recordings.json]
print(f"Using registry {reg_file}")
with open(reg_file) as json_data:
    register = json.load(json_data)
print(f"{register.keys()}")
new_item = {"name":args.name,
            "root":args.dest,
            "fs":args.fs,
            "color":args.colour,
            "dimensions":eval(args.dims),
            "source":eval(args.plume_source),
            "fields":args.fields.split(",")}

print(f"{new_item=}")

if len(args.source) == 0:
    args.source = args.name

print("Assuming {} contains probe files.".format(args.source))
# Check to see if there's a field in the registry with the same name
already_exists = []
new_registry = []
for item in register["registry"]:
    if "name" not in item: raise ValueError(f"Registry item {item} is missing 'name' field.")
    if "root" not in item: raise ValueError(f"Registry item {item} is missing 'root' field.")
    if ((item["name"]==new_item["name"]) and (item["root"] == new_item["root"])):
        already_exists.append(item)
    else:
        new_registry.append(item)
        

print(f"Found {len(already_exists)} items matching new item.")
if len(already_exists):
    print("Matches:")
    for ae in already_exists:
        print(ae)
        
if len(already_exists):
    if args.overwrite is True:
        print(f"Existing registry item with {args.name=} and {args.dest=} found. Overwriting it.")
        register["registry"] = new_registry
    else:
        print("Existing registry item found. Aborting.")
        
        exit(1)

if args.nocopy:
    print("Not copying probe files because --nocopy was set.")
else:
    # Make the dest dir: register["root"]/args.dest
    dest_dir = os.path.join(register["root"], args.dest)
    cmd = f"mkdir -p {dest_dir}"
    print(cmd)
    os.system(cmd)
    
    # Copy the files over: from args.source 
    cmd = f"cp {args.source}/probe*.* {dest_dir}"
    print(cmd)
    os.system(cmd)
    
print("Inserting new item:")
print(new_item)
register["registry"].append(new_item)

if not args.mock:
    with open(reg_file, "w") as json_data:
        json.dump(register, json_data, indent=4, sort_keys=True)
    print(f"Wrote registry to {reg_file=}.")
else:
    print(f"{args.mock=} so did not update registry.")

print("ALLDONE.")
