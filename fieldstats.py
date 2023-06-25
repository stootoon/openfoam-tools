"""
This script lists some statistics about the specified field at the specified time point.
If no time point is specified, the latest time point is used.
The statistics include the number of elements, the number of NaNs, the minimum, the 1st, 5th, 25th, 50th, 75th, 95th, 99th percentiles, and the maximum.
This is useful to check if the field is well-behaved, and to get an idea of the range of values.
The range of values is useful to know when setting the color ranges when generating PNGs of the field.

Usage:
    python fieldstats.py <field_name> [--time <time>]

Example:
    python fieldstats.py S1 --time 0.1   # Prints statistics for the field S1 at time 0.1
"""
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
    print(f"Computing stats for t ~= {t}")

    OF = openfoam.Case(mesh = openfoam.Mesh("mesh.p") if os.path.isfile("mesh.p") else None)
    
    field_name = args.fieldname
    if field_name not in OF.field_names:
        print(f"Specified field named '{field_name}' not found.")
        print(f"Available fields: {', '.join(OF.field_names)}")
        exit(1)
    

    F = OF.read_field(field_name, float(t))
    if len(F.shape) == 1:
        F = F[:, np.newaxis]

    for i in range(F.shape[1]):
        Fi = F[:,i]
        print("*"*40)
        print(f"DIMENSION {i}")
        print(f"{field_name} at t ~= {float(t)}")
        print("-"*40)
        print(f"{len(Fi)} elements.")
        print(f"{np.sum(np.isnan(Fi))} NaN.")
        print(f"Min: {np.nanmin(Fi)}")
        for p in [1,5,25,50,75,95,99]:
            print(f"{p:>3}: {np.nanpercentile(Fi,p)}")
        print(f"Max: {np.nanmax(Fi)}")
    

        
    

