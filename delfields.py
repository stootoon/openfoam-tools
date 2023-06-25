import argparse
parser = argparse.ArgumentParser()
parser.add_argument("delfields", type=str, help="List of fields to delete. If more than one, must be provided as a quoted space-separated list, e.g. \"S1 p U1\".")
parser.add_argument("--keepevery", type=float, help="Keep all the data for e.g. times 1,2,3, ...", default = 10)
parser.add_argument("--keeplastn", type=int, help="How many of the last time points to keep.", default = 5)
parser.add_argument("--startat", type=float, help="Starting time.", default = 0)
parser.add_argument("--endbefore", type=float, help="Delete all times up to but not including this.", default = 1e6)
args = parser.parse_args()


delfields = args.delfields.split(" ") 

delcmds = ["rm -f {}; rm -f {}.gz".format(f,f) for f in delfields]
print(delfields)
print(delcmds)
import re, os
import numpy as np
from utils import get_numerical_directories
from tqdm import tqdm

time_vals, time_dirs = get_numerical_directories()
if len(time_vals) < 1:
    raise Exception("No time directories found. Are you at the top level of a case?")

times_to_keep = sorted(list(set(list(np.arange(time_vals[0], time_vals[-1], args.keepevery)) + time_vals[-args.keeplastn:])))
for tv, td in tqdm(zip(time_vals, time_dirs)):
    if tv < args.startat or tv >= args.endbefore:
        continue
    if tv in times_to_keep:
        print("Keeping everything for time {} (dir {})".format(tv, td))
    else:
        cmds = ["cd {}".format(td)] + delcmds + ["cd .."]
        cmd = "; ".join(cmds)
        os.system(cmd)
        
        

        
                
        

