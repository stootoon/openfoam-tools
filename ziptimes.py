import argparse
parser = argparse.ArgumentParser()
parser.add_argument("--tmin", type=float, help="Times after tmin will be zipped.", default = 0)
parser.add_argument("--tmax", type=float, help="Times before tmax (inclusive) will be zipped.", default = 100000)
parser.add_argument("--dt",   type=float, help="The stepsize to use.", default = 0.001)
parser.add_argument("--delete", help="Whether to delete the folder after zipping.", action="store_true")
args = parser.parse_args()

print(args)

import re, os
dirs = next(os.walk('.'))[1]
use = []
print("Found {} total directories.".format(len(dirs)))
for i, d in enumerate(sorted(dirs)):
    if re.match("[0-9]+\.?[0-9]*", d): # It's a numerical directory
        v = float(d)
        if v > args.tmin and v <= args.tmax:
            use.append((d,v))
    else:
        print("Skipping {:<16} because it's not a numerical directory.".format(d))

use = sorted(use, key = lambda u: u[1])
print("{} directories included.".format(len(use)))
if len(use):
    print("First: {:>8}".format(use[0][0]))
    print("Last:  {:>8}".format(use[-1][0]))
    for dd, dv in use:
        cmd = "tar -zcvf {}.tar.gz {}".format(dd, dd)
        os.system(cmd)
        print(cmd)
        if args.delete:
            cmd = "rm -rf {}".format(dd)
            os.system(cmd)
            print(cmd)
else:
    print("No numerical directories found in range.")
            
        
                
        

