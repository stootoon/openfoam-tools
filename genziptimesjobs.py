import os, sys, argparse

parser = argparse.ArgumentParser(description = "Generates a bunch of scripts for zipping up the times directories in the current folder.")
parser.add_argument("--tmin", help="Minimum time to compress.", type=float, default=0)
parser.add_argument("--tmax", help="Maximum time to compress.", type=float, default=1e6)
parser.add_argument("--nperjob", help="Number of compressions per job.", type = int, default = 10)
args = parser.parse_args()

sys.path.append(os.getenv("CFDGITPY"))
from functools import reduce

header = """#!/bin/bash
# Simple SLURM sbatch example
#SBATCH --job-name=JOBNAME
#SBATCH --ntasks=1
#SBATCH --time=96:00:00
#SBATCH --mem-per-cpu=32G
#SBATCH --partition=compute

ml purge > /dev/null 2>&1
python -u $CFDGITPY/ziptimes.py --tmin TMIN --tmax TMAX --delete
"""

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
jobs = [use[i:i+args.nperjob+1] for i in range(0, len(use), args.nperjob)]
for i, job in enumerate(jobs):
    job_file = "job{}.sh".format(i) 
    job_name = "zt{}".format(job[0][0])
    with open(job_file, "w") as out_file:
        content = reduce(lambda h, pair: h.replace(pair[0], pair[1]), 
                         [("JOBNAME", job_name), 
                          ("TMIN",    job[0][0]), 
                          ("TMAX",    job[-1][0])], 
                         header)
        out_file.write(content)
        print("{:>12}: {:8.3f},  {:8.3f}".format(job_file, job[0][1], job[-1][1]))
    
