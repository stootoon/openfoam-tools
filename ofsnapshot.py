import os, sys
import argparse

parser = argparse.ArgumentParser(description="Snapshot the specified field and produce an image. Run from inside a case folder.")
parser.add_argument("fieldname", help="The name of the field to use.")
parser.add_argument("--extension", type = str, help="The extension of the output file. PNG by default. Set to 'p' to get values stored as an array.", default="png")
parser.add_argument("--noaxis", help="Whether to remove axes in the plot.", dest='noaxis', action="store_true")
parser.add_argument("--vmin", type = str, help="Minimum value to plot.", default="1%")
parser.add_argument("--vmax", type = str, help="Maximum value to plot.", default="99%")
parser.add_argument("--latest", help="Whether to plot just the latest timestep", dest="latest", action="store_true")
parser.add_argument("--times",  help="Specific time points to plot, given as a comma separated list with NO SPACES. Overriden by '--latest'.", type=str, default="")
parser.add_argument("--dpi",  help="Figure dots per inch. Defaults to -1 (use the figure default).", type=int, default=-1)
parser.add_argument("--cmap",  help="Colormap to use.", type=str, default="jet")
parser.add_argument("--dim",  help="The dimension to plot (for vector fields).", type=int, default=0)
args = parser.parse_args()

sys.path.append(os.getenv("CFDGITPY"))
from external import Ofpp
import openfoam as openfoam
from datetime import datetime

if len(sys.argv)<=1:
    print("Usage: ofsnapshot [FIELDNAME] {timepoint}")
    print("")
    print("Run from inside a case folder.")
    print("By default snapshots will be created for all time points.")
    exit()

with openfoam.TimedBlock("SNAPSHOT_MAIN"):
    OF = openfoam.Case(mesh = openfoam.Mesh("mesh.p") if os.path.isfile("mesh.p") else None)
    
    field_name = args.fieldname
    if field_name not in OF.field_names:
        print("Specified field named '{}' not found.".format(field_name))
        print("Available fields: {}".format(", ".join(OF.field_names)))
        exit(1)
    
    print("Taking snapshot of field {}.".format(field_name))
    print("Output format: {}".format(args.extension))

    make_image = True
    if args.extension == "p":
        print("Outputting values not an image.")
        make_image = False
        import pickle
    else:
        print(f"Outputting an image. Using {args.vmin=} and {args.vmax=} and {args.dpi=} and {args.cmap=}")
        import matplotlib as mpl
        mpl.use("Agg")
        from matplotlib import pyplot as plt
        from matplotlib.ticker import NullLocator

    
    if args.latest:
        print("Creating snapshot for LATEST time point.")
        time_vals = [OF.time_vals[-1]]
    elif args.times:
        time_vals = [float(t) for t in args.times.split(",")]
        print("Creating snapshot for SPECIFIC timepoints: {}.".format(time_vals))
    else:
        print("Creating snapshots for ALL time points.")
        time_vals = OF.time_vals

    with openfoam.TimedBlock("CREATING SNAPSHOTS"):
        print("Creating snapshots for times {} - {} ({} snapshots).".format(time_vals[0], time_vals[-1], len(time_vals)))
        print("Using dimension {}".format(args.dim))        
        for t in time_vals:
            if t == 0:
                print("Skipping 0")
                continue

            print(t,)
            file_name = "{}_d{}_{:07.3f}".format(field_name, args.dim, t)
            file_name = file_name.replace(".", "") + "." + args.extension # Don't keep the decimal, it causes problems when making movies.

            if make_image:
                
                plt.figure(figsize=(6,16))                
                OF.plot_field(field_name, t, vmin=args.vmin, vmax=args.vmax, cmap = args.cmap, dim=args.dim)
                if args.noaxis:
                    print("Ploting with no axes.")
                    plt.gca().axis("off")
                    plt.gca().xaxis.set_major_locator(NullLocator())
                    plt.gca().yaxis.set_major_locator(NullLocator())
                    if args.dpi>0:
                        plt.savefig(file_name, bbox_inches="tight", pad_inches = -0.05, dpi=args.dpi)
                    else:
                        plt.savefig(file_name, bbox_inches="tight", pad_inches = -0.05)
                else:
                    if args.dpi>0:
                        plt.savefig(file_name, bbox_inches="tight", dpi=args.dpi)
                    else:
                        plt.savefig(file_name, bbox_inches="tight")
                plt.close("all")
            else:
                FF,*_ = OF.snapshot_field(field_name, t)
                FF = FF if len(FF.shape)==2 else FF[:,:,args.dim]
                with open(file_name, "wb") as f:
                    pickle.dump(FF, f)
                
            print(f"Wrote {file_name=}")
                
print("ALLDONE")






