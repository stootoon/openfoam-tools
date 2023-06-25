import os, sys, argparse


parser = argparse.ArgumentParser(description = "Lists some statistics about the specified field at the specified time point.")
parser.add_argument("fieldname",  help="Field to snapshot", type=str)
parser.add_argument("--time", help="Time point to examine. Default takes the latest time", type=float, default=-1)
args = parser.parse_args()

import numpy as np
sys.path.append(os.getenv("CFDGITPY"))
import openfoam


with openfoam.TimedBlock("FIELDSTATS"):

    t = np.max(openfoam.Case.get_output_times()[0]) if args.time <= 0 else args.time
    print("Computing stats for t ~= {}".format(t))

    OF = openfoam.Case(mesh = openfoam.Mesh("mesh.p") if os.path.isfile("mesh.p") else None)
    
    field_name = args.fieldname
    if field_name not in OF.field_names:
        print("Specified field named '{}' not found.".format(field_name))
        print("Available fields: {}".format(", ".join(OF.field_names)))
        exit(1)
    

    F = OF.read_field(field_name, float(t))
    if len(F.shape) == 1:
        F = F[:, np.newaxis]

    for i in range(F.shape[1]):
        Fi = F[:,i]
        print("*"*40)
        print("DIMENSION {}".format(i))
        print("{} at t ~= {}".format(field_name, float(t)))
        print("-"*40)
        print("{} elements.".format(len(Fi)))
        print("{} NaN.".format(np.sum(np.isnan(Fi))))
        print("Min: {}".format(np.nanmin(Fi)))
        for p in [1,5,25,50,75,95,99]:
            print("{:>3}: {}".format(p, np.nanpercentile(Fi,p)))
        print("Max: {}".format(np.nanmax(Fi)))
    

        
    

