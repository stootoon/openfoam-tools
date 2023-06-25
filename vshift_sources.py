import os, sys
import argparse
import numpy as np

parser = argparse.ArgumentParser(description="Generates a bunch of cases in which a source is vertically shifted by fixed amounts. The cases are named BASE_CASE_Y1.0 etc., where BASE_CASE is the name of the base case but with any trailing '_base' removed.")
parser.add_argument("base_case",   help="Name of the base case to use.",   type = str)
parser.add_argument("--field",     help="Name of the field in the base case to use. Must contain YMIN and YMAX in its 0 file.", type = str, default = "S1")
parser.add_argument("--width",     help="The width of the source in meters. Defaults to 0.01.", type = float, default = 0.01)
parser.add_argument("yfirst",      help="The center of the first source.", type = float)
parser.add_argument("ylast",       help="The center of the last source.",  type = float)
parser.add_argument("num_sources", help="The number of sources.",          type = int)
parser.add_argument("--remove", help="Whether to first remove the existing target case directories.", action = "store_true")
args = parser.parse_args()
print(args)

yfirst  = args.yfirst
ylast  = args.ylast
width = args.width
num_sources = args.num_sources
centers = [round(c,3) for c in np.linspace(yfirst, ylast, num_sources)]
ranges  = [(round(c-width/2,3), round(c + width/2,3)) for c in centers]
print(centers)
print(ranges)

def sys(cmd):
    print(cmd)
    os.system(cmd)

if not os.path.isdir(args.base_case):
    print("Could not find base case with name %s" % (args.base_case))
    exit(1)

source_case = args.base_case
target_prefix = source_case.replace("_base", "")

for i, (ymin,ymax) in enumerate(ranges):
    print("")
    target_case = "{}_Y{:1.3f}".format(target_prefix, centers[i])
    if args.remove:
        sys("rm -rf %s" % (target_case))
    sys("copycase %s %s" % (source_case, target_case))
    sys("sed s/YMIN/%1.3f/g -i %s" % (ymin, os.path.join(target_case, "0", args.field)))
    sys("sed s/YMAX/%1.3f/g -i %s" % (ymax, os.path.join(target_case, "0", args.field)))
    sys("sed s/JOBNAME/%s/g -i %s" % ("Y%1.3f" % (centers[i]), os.path.join(target_case, "run.sh")))
    
    
# if not os.path.isfile("S0"):
#     print("Could not find S0 in current directory. Exiting.")
#     exit(1)
    
# for i, (ymin, ymax) in enumerate(ranges):
#     cmd = 'sed s/S0/S{}/g S0 > S{}; sed -i s/YMIN/{}/g S{}; sed -i s/YMAX/{}/g S{};'.format(i+1, i+1, ymin, i+1, ymax, i+1)    
#     print(cmd)
#     os.system(cmd)
