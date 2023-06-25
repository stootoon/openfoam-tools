import argparse

parser = argparse.ArgumentParser()
parser.add_argument("--files", help="List the files instead of directories.",       action="store_true")
args = parser.parse_args()
import os
root, dirs, files = next(os.walk("."))
if args.files:
    for f in sorted(files):
        print(f)
else:
    for d in sorted(dirs):
        print(d)

