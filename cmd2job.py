import os
import argparse

parser = argparse.ArgumentParser("Generates a job script for running the specified command that can be submitted to slurm.")
parser.add_argument("cmd", help="The command to be run.", type=str)
parser.add_argument("--jobname", help="The name of the job.", type=str, default="cmd")
parser.add_argument("--jobfile", help="The file the job will be written to.",       type=str, default="job.sh")
parser.add_argument("--jobtime", help="The amount of time required for the job.",   type=str, default="1-0")
parser.add_argument("--jobmem",  help="The amount of memory required for the job.", type=str, default="32G")
parser.add_argument("--submit",  help="Submit the job once created.", action="store_true")
args = parser.parse_args()

content= """#!/bin/bash
# Simple SLURM sbatch example
#SBATCH --job-name={jobname}
#SBATCH --ntasks=1
#SBATCH --time={jobtime}
#SBATCH --mem-per-cpu={jobmem}
#SBATCH --partition=cpu

ml purge > /dev/null 2>&1
{cmd}
""".format(jobname=args.jobname, jobtime=args.jobtime, jobmem=args.jobmem, cmd=args.cmd)

with open(args.jobfile, "w") as f:
    f.write(content)

print("Wrote {}.".format(args.jobfile))
if args.submit:
    os.system("sbatch {}".format(args.jobfile))
print("ALLDONE")
