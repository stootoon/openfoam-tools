import argparse
parser = argparse.ArgumentParser(description="Generates a jobs that use tar to decompress specific fields from compressed time folders into the CURRENT directory.")
parser.add_argument("field",     help="Field to decompress", type = str)
parser.add_argument("source",    help="The source folder containing the compressed data.", type=str)
parser.add_argument("--tmin",    type=float, help="Minimum time to decompress. Times >  tmin will be decompressed.",  default = 0)
parser.add_argument("--tmax",    type=float, help="Minimum time to decompress. Times <= tmax will be decompressed.",  default = 1e6)
parser.add_argument("--nperjob", help="Number of decompressions per job.", type = int, default = 1000)
args = parser.parse_args()

import os, sys

sys.path.append(os.getenv("CFDGITPY"))
import utils

header = """#!/bin/bash
# Simple SLURM sbatch example
#SBATCH --job-name=((jobname))
#SBATCH --ntasks=1
#SBATCH --time=24:00:00
#SBATCH --mem-per-cpu=16G
#SBATCH --partition=cpu

ml purge > /dev/null 2>&1
python -u $CFDGITPY/decompress_field.py {field} {source} --tmin ((tmin)) --tmax ((tmax))
""".format(field=args.field, source=args.source).replace("((","{").replace("))","}")


tv, tf = utils.get_numerical_files(case_path = args.source)
print("Found {} total compressed files.".format(len(tv)))
use = [(tf[i], v) for i,v in enumerate(tv) if v > args.tmin and  v <= args.tmax]
print("Found {} files for the time interval ({:.3f} - {:.3f}].".format(len(use), args.tmin, args.tmax))
if not len(use):
    print("No files available to decompress.")
    exit(1)
print("First: {:>16}".format(use[0][0]))
print(" Last: {:>16}".format(use[-1][0]))

jobs = [use[i:i+args.nperjob+1] for i in range(0, len(use), args.nperjob)]
for i, job in enumerate(jobs):
    job_file = "job{}.sh".format(i) 
    job_name = "d{}".format(job[0][1])
    with open(job_file, "w") as out_file:
        content = header.format(jobname=job_name, tmin=job[0][1], tmax=job[-1][1])
        out_file.write(content)
        print("{:>12}: {:>8.3f} to {:8.3f}".format(job_file, job[0][1], job[-1][1]))

