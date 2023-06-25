import os, sys
sys.path.append(os.getenv("CFDGITPY"))
import utils as utils
import argparse

parser = argparse.ArgumentParser(description="Parallel reconstructPar the data for the current case. Must be run from the top level of a case.")
parser.add_argument("--njobs", type = int, help="Number of jobs to generate.", default=50)
args, unknown_args = parser.parse_known_args()

if not os.path.isdir("processor0"):
    print "Could not find 'processor0' directory. Exiting."
    exit(1)

if not os.path.isdir("0"):
    print "No '0' directory found. Run from the root folder of an OpenFOAM case. Exiting."
    exit(1)

time_vals_avail, time_dirs_avail = utils.get_numerical_directories(case_path = "processor0")
time_vals_done, time_dirs_done   = utils.get_numerical_directories(case_path = ".")

time_dirs_todo = sorted(list(set(time_dirs_avail) - set(time_dirs_done)), key = float)
print "Found {} directories to reconstruct.".format(len(time_dirs_todo))

time_dirs_per_job = [time_dirs_todo[i::args.njobs] for i in range(args.njobs)]

job_text = """#!/bin/bash
# Simple SLURM sbatch example
#SBATCH --job-name=recpID
#SBATCH --ntasks=1
#SBATCH --time=14-0
#SBATCH --mem-per-cpu=32G
#SBATCH --partition=compute

ml purge > /dev/null 2>&1
ml OpenFOAM/6-foss-2018b
source $FOAM_BASH
reconstructPar -newTimes -time 'TIMES'
"""

for i, job_dirs in enumerate(time_dirs_per_job):
    file_name = "job{}.sh".format(i)
    with open(file_name, "w") as out_file:
        out_file.write(job_text.replace("TIMES", ",".join(job_dirs)).replace("ID", str(i)))

print "Wrote {} jobs.".format(len(time_dirs_per_job))


