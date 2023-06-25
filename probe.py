import os, sys, re
import argparse

parser = argparse.ArgumentParser(description="Probe a field in the current case at specified locations.")
parser.add_argument("fieldname", help="The name of the field to use.")
parser.add_argument("--nx",     type = int, help="Number of x coordinates.", default=11)
parser.add_argument("--ny",     type = int, help="Number of y coordinates.", default=11)
parser.add_argument("--xmin",   type = str, help="Minimum x coordinate to use. Can be absolute or %% if suffixed with %%.", default="0%")
parser.add_argument("--xmax",   type = str, help="Maximum x coordinate to use. Can be absolute or %% if suffixed with %%.", default="100%")
parser.add_argument("--ymin",   type = str, help="Minimum y coordinate to use. Can be absolute or %% if suffixed with %%.", default="0%")
parser.add_argument("--ymax",   type = str, help="Maximum y coordinate to use. Can be absolute or %% if suffixed with %%.", default="100%")
parser.add_argument("--tmin",   type = float, help="Minimum time to probe. Output will include t>=tmin. Default = 0",      default=0)
parser.add_argument("--tmax",   type = float, help="Maximum time to probe. Output will include t< tmax. Default = 100000", default=1000000)
parser.add_argument("--coords", type = str, help="""Specify the coordinates directly. The trailing arguments in the form "(x_1, y_1) (x_2, y_2) ..." are interpreted as coordinates for the probes. Can be supplied as absolute or relative if suffixed with %%. E.g. (2.1, 40%%) will place a probe at x = 2.1m and y = 40%% of the full height.""", default = None)
parser.add_argument("--mock", action="store_true", help="Will setup the probes but will not actually read any data. Coordinates and times will still be written.")
args = parser.parse_args()
print(args)

print("Importing openfoam modules.")
from datetime import datetime
sys.path.append(os.getenv("CFDGITPY"))
from external import Ofpp
import openfoam as openfoam
import pickle
import numpy as np

OF = openfoam.Case()

xrange = OF.mesh.x_range
yrange = OF.mesh.y_range

c2abs = lambda c, crange: float(c[:-1])*(crange[1] - crange[0])/100. + crange[0] if c[-1] == "%" else float(c)

def validate_coord(c, crange, tol=1e-6): 
    if c>=crange[0] and c<=crange[1]:
        return c
    elif c<crange[0] and crange[0]-c < tol:
        return crange[0]
    elif c>crange[1] and c-crange[1] < tol:
        return crange[1]
    raise ValueError("Coordinate {} is out of range of {}.".format(c,crange))

# Setup the minima and maxima
print("Setting xmin.")
xmin = validate_coord(c2abs(args.xmin, xrange), xrange)
print("Setting xmax.")
xmax = validate_coord(c2abs(args.xmax, xrange), xrange)
if xmin >= xmax:
    raise ValueError("xmin {} >= xmax {}.".format(xmin, xmax))
xrange = (xmin, xmax)
print("xrange: {}".format(xrange))

print("Setting ymin.")
ymin = validate_coord(c2abs(args.ymin, yrange), yrange)
print("Setting ymax.")
ymax = validate_coord(c2abs(args.ymax, yrange), yrange)
if ymin >= ymax:
    raise ValueError("ymin {} >= ymax {}.".format(ymin, ymax))
yrange = (ymin, ymax)
print("yrange: {}".format(yrange))

x2abs = lambda x: validate_coord(c2abs(x, xrange), xrange)
y2abs = lambda y: validate_coord(c2abs(y, yrange), yrange)

if args.coords:
    # parse the coordinates
    print("Parsing coordinates from: {}".format(args.coords))
    coords = []
    for match in re.finditer("\(([^\)]+)\)", args.coords):
        s = match.group(1).split(",")
        if len(s)<2:
            raise ValueError("Malformed coordinate {}".format(match.group(0)))
        coords.append((x2abs(s[0]), y2abs(s[1])))
    print(coords)
else:
# Set the coordinates based on nx and ny
    dx = 0 if args.nx <=1 else (xrange[1] - xrange[0])/(args.nx-1)
    dy = 0 if args.ny <=1 else (yrange[1] - yrange[0])/(args.ny-1)
    coords = [(xrange[0] + dx*ix, yrange[0] + dy*iy, 0) for iy in range(args.ny) for ix in range(args.nx)]

print("Probing field {} at {} coordinates.".format(args.fieldname, len(coords)))
for coord in coords:
    OF.add_probe(args.fieldname, coord, coord_mode = "absolute")

if not args.mock:
    OF.read_probes(tmin = args.tmin, tmax = args.tmax)
    probe_t      = [float(tstr) for tstr in OF.probes[0].t]
else:
    print(f"{args.mock=} so no probe data was actually read.")

probe_coords = [p.coord for p in OF.probes]
with open("probe.coords.p", "wb") as out_file:
    pickle.dump(probe_coords, out_file)

if not args.mock:
    with open("probe.t.p", "wb") as out_file:
        pickle.dump(probe_t, out_file)
    
    probe_data   = np.stack([p.data for p in OF.probes], axis=1)
    assert probe_data.shape[0] == len(probe_t),      f"{probe_data.shape[0]=} <> {len(probe_t)=}."
    assert probe_data.shape[1] == len(probe_coords), f"{probe_data.shape[1]=} <> {len(probe_coords)=}."    
    np.save("probe.data.npy", probe_data)

print("ALLDONE")



