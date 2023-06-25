import os, sys, argparse

parser = argparse.ArgumentParser(description = "Generates a bunch of scripts taking snapshots of the specified field for the current case. Produces a bunch of job*.sh scripts ready to be sbatch'd.")
parser.add_argument("field",  help="Field to snapshot", type=str)
parser.add_argument("--tmin", help="Minimum time for snapshot.", type=float, default=0)
parser.add_argument("--tmax", help="Maximum time for snapshot.", type=float, default=1e6)
parser.add_argument("--vmin", help="Minimum value to plot.", type=str, default="5%")
parser.add_argument("--vmax", help="Maximum value to plot.", type=str, default="95%")
parser.add_argument("--every", help="Time step in seconds if float or number of frames if integer.", type = str, default="1")
parser.add_argument("--dpi",  help="Image dpi. -1 (default) means use the default image dpi.", type=int, default=-1)
parser.add_argument("--noaxis", help="Whether to hide the axes in the plots.", dest="noaxis", action="store_true")
parser.add_argument("--nperjob", help="Number of snapshots per job.", type = int, default = 10)
parser.add_argument("--cmap", help="Colormap to use.", type=str, default="gray")
parser.add_argument("--dim", help="The dimension to use.", type=int, default=0)
args = parser.parse_args()

sys.path.append(os.getenv("CFDGITPY"))
from utils import get_numerical_directories
from functools import reduce

header = """#!/bin/bash
# Simple SLURM sbatch example
#SBATCH --job-name=JOBNAME
#SBATCH --ntasks=1
#SBATCH --time=24:00:00
#SBATCH --mem-per-cpu=16G
#SBATCH --partition=cpu

ml purge > /dev/null 2>&1
conda activate py36
python -u $CFDGITPY/ofsnapshot.py FIELD NOAXIS --vmin VMIN --vmax VMAX --times TIMES --dpi DPI --cmap CMAP --dim DIM
""".replace("VMIN", args.vmin).replace("VMAX", args.vmax).replace("NOAXIS", "--noaxis" if args.noaxis else "")

time_vals, time_dirs = get_numerical_directories()
vd = sorted(zip(time_vals, time_dirs), key = lambda x: x[0])
for i, (tv, td) in enumerate(vd):
    if tv > 0:
        break

times = [vd[i]]
every = int(1/float(args.every) if "." in args.every else args.every)
print("Capturing every {} frames.".format(every))
times = vd[1::every]
# for j in range(i+1,len(vd), every):
#     if vd[j][0] - times[-1][0] < args.dt:
#         continue
#     times.append(vd[j])

#times = [(v,d) for (v,d) in zip(time_vals, time_dirs) if v!=0 and v>=args.tmin and v<=args.tmax]

jobs  = [times[i:i+args.nperjob] for i in range(0, len(times), args.nperjob)]

for i, job in enumerate(jobs):
    job_file = "job{}.sh".format(i) 
    job_times = [j[0] for j in job]
    job_name = "{}_{}".format(args.field, job_times[0])
    with open(job_file, "w") as out_file:
        content = reduce(lambda h, pair: h.replace(pair[0], pair[1]), 
                         [("JOBNAME", job_name), 
                          ("FIELD",   args.field), 
                          ("VMIN",    args.vmin), 
                          ("VMAX",    args.vmax),
                          ("DPI",     str(args.dpi)),
                          ("CMAP", args.cmap),
                          ("DIM", str(args.dim)),
                          ("TIMES", ",".join(map(str, job_times)))], 
                         header)
        out_file.write(content)
        print(job_file)
        
    

