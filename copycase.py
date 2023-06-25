import os, sys
import argparse
from utils import get_numerical_directories
from tqdm import tqdm

def cmd(c):
    print(c)
    os.system(c)

parser = argparse.ArgumentParser(description="Copy an OpenFOAM case to a new folder. By default only the initial condition folders are copied.")
parser.add_argument("source",    type=str, help="The folder containing the case to copy.")
parser.add_argument("--dest",    type=str, help="Name of the folder to copy the case into. By default 'copy' is appended to the source name.")
parser.add_argument("--full",    action="store_true", help="Whether to fully copy the case.")
parser.add_argument("--unzip",   action="store_true", help="Whether to unzip field data after copying.")
parser.add_argument("--fields",  type=str, help="Comma separated list of specific fields to copy. By default everything is copied.")
parser.add_argument("--folders", type=str, help="Comma separated list of specific folders to copy.")
args = parser.parse_args()

print(args)
time_vals, time_dirs = get_numerical_directories(case_path = args.source)
print("{} time directories found. ".format(len(time_vals)))
print("{} - {}.".format(time_vals[0], time_vals[-1]))

print("Copying from {}".format(args.source))
dest = args.source + "_copy" if args.dest is None else args.dest
print("Copying   to {}".format(dest))
#if args.dest is None:

source = args.source
cmd("mkdir -p {}".format(dest))
cmd("cp -R {}/system {}".format(source, dest))
cmd("cp -R {}/constant {}".format(source, dest))
cmd("cp {}/*.foam {}".format(source, dest))
cmd("cp {}/Allclean {}".format(source, dest))
cmd("cp {}/run.sh {}".format(source, dest))
cmd("cp -R {}/0 {}".format(source, dest))

fields = [f.strip() for f in args.fields.split(",")] if args.fields is not None else "ALL"

# Build a list of files to copy by cycling through each folder.
print("Building file list.")
folders = args.folders.split(",") if args.folders is not None else time_dirs
print("Examining {} directories.".format(len(folders)))
files = []
unique_folders = set()
i = 0
for folder in tqdm(folders):
    folder_path = os.path.join(source, folder)
    root, dirs, folder_files = next(os.walk(folder_path))
    files_to_append = folder_files if fields == "ALL" else [f for f in folder_files if any([f.endswith(fld) or f.endswith(fld+".gz") for fld in fields])]
    files += [(source, folder, fi) for fi in files_to_append]
    unique_folders |= {folder}

unique_folders = list(unique_folders)
print("Found {} files in {} folders.".format(len(files), len(unique_folders)))
print("Making target folders.")
for folder in tqdm(unique_folders):
    os.system("mkdir -p {}/{}".format(dest, folder))
print("Copying files.")
for (src, fld, f) in tqdm(files):
    os.system("cp {}/{}/{} {}/{}/{}".format(src,fld,f,dest,fld,f))
    if args.unzip and f.endswith(".gz"):
        os.system("gzip -d {}/{}/{}".format(dest,fld,f))

print("ALLDONE.")
