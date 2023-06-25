import os, sys, re, pdb
from external import Ofpp
import numpy as np
from collections import namedtuple
from scipy.interpolate import griddata
from matplotlib import pyplot as plt
import time
from datetime import datetime
import pickle
from copy import deepcopy
import argparse
import pdb

from utils import TimedBlock, get_numerical_directories

def run_case(case_root, mesh_file, solver_name):
    """
    Runs the specified case using the specified mesh and solvers.
    The mesh_file must be a gmsh .msh file.
    """

    cwd = os.getcwd()    
    # Copy the mesh file to the case root.

    print("Copying mesh file to the case root.")
    cmd = "cp -f {} {}".format(mesh_file, case_root)
    print(cmd)
    if os.system(cmd):
        raise Exception("Failed executing command: %s" % (cmd))
    
    print("Changing directory to case root.")
    os.chdir(case_root)
    
    print("Running gmshToFoam.")
    cmd = "gmshToFoam {} > output.log"
    print(cmd)
    if os.system(cmd):
        raise Exception("Failed executing command: %s" % (cmd))
    
    print("Checking gmshToFoam output.")
        

def fix_polyMesh_boundary_file(items, case_root = ".", create_backup = True):
    # parse boundary file
    new_lines = []
    state = None
    boundary_file = os.path.join(case_root, "constant", "polyMesh", "boundary")
    with open(boundary_file, "r") as in_file:
        print("Reading %s" % (boundary_file))
        for line_no, line in enumerate(in_file):
            for key in items:
                if key in line:
                    state = key
            if "}" in line:
                state = None
            new_lines.append(line if not state else re.sub(r"([A-Z|a-z]+)ype([ ]+)[a-z]+;", "\\1ype\\2%s;" % items[state], line))
            if new_lines[-1] != line:
                print("LINE:  %d" % (line_no))
                print("STATE: %s" % (state))
                print("old: %s" % (line),)
                print("new: %s" % (new_lines[-1]))
    
    if create_backup:
        os.system("mv {} {}.bak".format(boundary_file, boundary_file))
    with open(boundary_file, "w") as out_file:
        out_file.write("".join(new_lines))
    print("Wrote {}.".format(boundary_file))

def coord2str(x,y,z):
    return "({:.3f}, {:.3f}, {:.3f})".format(x,y,z) if z else "({:.3f}, {:.3f})".format(x,y)

class Mesh:
    def log(self, msg):
        print(msg)

    def __init__(self, path):
        with TimedBlock("LOADING MESH FROM {}".format(path), self.log):
            if os.path.isdir(path):
                self.log("Specified path is a directory, assuming it's an OpenFOAM case root and reading the mesh from it.")
                self.log("Reading mesh from '%s'." % path)
                self.path = path            
                self.mesh = Ofpp.FoamMesh(self.path)
                self.log("%d faces found. Computing face centers..." % (len(self.mesh.faces)))
                self.face_centers = np.array([np.mean(self.mesh.points[f,:],  axis=0) for f in self.mesh.faces])
                self.log("%d cells found. Computing cell centers..." % (len(self.mesh.cell_faces)))
                self.cell_centers = np.array([np.mean(self.face_centers[c,:], axis=0) for c in self.mesh.cell_faces])
                self.x_range = (min(self.cell_centers[:,0]), max(self.cell_centers[:,0]))
                self.y_range = (min(self.cell_centers[:,1]), max(self.cell_centers[:,1]))
                self.z_range = (min(self.cell_centers[:,2]), max(self.cell_centers[:,2]))        
                self.log("X range: {}.".format(self.x_range))
                self.log("Y range: {}.".format(self.y_range))
                self.log("Z range: {}.".format(self.z_range))
            elif os.path.isfile(path):
                self.log("Specified path is a file, assuming it's a pickled Mesh object and attempting to load it.")
                self.load_from_file(path)
            else:
                raise ValueError("Specified path is neither a file nor a directory, don't know what to do!")
    
    def coord2index(self, x, y, z = None):
        self.log("Mapping coordinates to data index.")
        d2 = (x - self.cell_centers[:,0])**2 + (y - self.cell_centers[:,1])**2
        if z:
            d2 += (z - self.cell_centers[:,2])**2
        ind = np.argmin(d2)
        self.log("Desired coordinates: {}.".format(coord2str(x,y,z)))
        self.log("Closest cell center: {}.".format(coord2str(*tuple(self.cell_centers[ind,:]))))
        self.log("Index %d." % (ind))
        return ind

    def save_to_file(self, path):
        with TimedBlock("Saving Mesh to file {}.".format(path), self.log):
            with open(path, "wb") as f:
                pickle.dump(self.__dict__, f, pickle.HIGHEST_PROTOCOL)

    def load_from_file(self, path):
        with TimedBlock("Loading mesh from file {}.".format(path), self.log):
            with open(path, "rb") as f:
                d = pickle.load(f)
                self.__dict__.update(d)
        

class Probe:
    def log(self, msg):
        print(msg)

    def __init__(self, case, field, coord,  coord_mode = "relative", name = None, color = None):
        self.log("\nINITIALIZING NEW PROBE.")
        self.name  = name  if name  else "%s_%d" % (field, sum([p.field == field for p in case.probes]) + 1)
        self.color = color if color else plt.cm.hsv(np.random.rand())
        self.coord = list(coord)
        if coord_mode.lower() == "relative":
            self.log("Mapping relative coordinates to absolute.")
            self.coord[0] = coord[0]*(case.mesh.x_range[1] - case.mesh.x_range[0]) + case.mesh.x_range[0]
            self.coord[1] = coord[1]*(case.mesh.y_range[1] - case.mesh.y_range[0]) + case.mesh.y_range[0]
            self.coord[2] = coord[2]*(case.mesh.z_range[1] - case.mesh.z_range[0]) + case.mesh.z_range[0]
        self.coord = tuple(self.coord)
        self.index = case.mesh.coord2index(*self.coord)
        self.field = field
        self.data  = []
        self.t     = []
        self.case = case
        self.log("    Name: %s" % (self.name))
        self.log("   Color: {}".format(self.color))
        self.log("   Field: %s" % (self.field))
        self.log("   Coord: {}".format(self.coord))
        self.log("   Index: %d" % (self.index))
        self.log("    Case: %s" % (self.case.name))

    def __str__(self):
        return "\n".join([
            "PROBE %s" % (self.name),
            "Field: %s" % (self.field),
            "Coord: {}".format(self.coord),
            "Index: %d" % (self.index),
            "t: {}".format( ( "%1.3f - %1.3f" % (self.t[0], self.t[-1]) ) if self.t else "None"),
            "data: {}".format("{}".format (self.data)),
            "Case: %s" % (self.case.name),                          
            "Color: {}".format(self.color),
        ])
    
    def __repr__(self):
        return self.__str__()


class Case:
    @classmethod
    def get_output_times(cls, case_path = "."):
        return get_numerical_directories(case_path = case_path)
            
    def __init__(self, name = None, case_path = ".", num_dims = 2, mesh = None, verbosity = 1):
        self.name = name if name else os.path.basename(os.path.abspath(case_path))
        self.path = case_path
        self.verbosity = verbosity
        self.num_dims = num_dims
        self.probes = []
        with TimedBlock("Initializing %dD OpenFOAMCase called '%s' located at '%s'." % (self.num_dims, self.name, self.path), self.log):

            if mesh:
                if type(mesh) in [str, unicode]:
                    self.log("Constructing mesh from path {}".format(mesh))
                    self.mesh = Mesh(mesh)
                else:
                    self.log("Using specified Mesh object.")
                    self.mesh = deepcopy(mesh)                
            else:
                self.log("No mesh specified, reading from case.")
                self._read_mesh()
            self._read_output_times()
            self._read_field_names()
            self.log("DONE loading case.")
    

    def log(self, msg):
        (self.verbosity > 0)  and print(msg)

    def _read_output_times(self):
        self.log("LOADING TIMES.")
        self.time_vals, self.time_dirs = Case.get_output_times(self.path)
        self.log("%d time points found, from %6.3f - %6.3f." % (len(self.time_dirs), min(self.time_vals), max(self.time_vals)))
        self.log("Temporal resolution: %6.3f +/- %6.3f sec." % (np.mean(np.diff(self.time_vals)), np.std(np.diff(self.time_vals))))

    def _read_field_names(self):
        self.log("READING FIELD NAMES.")
        self.field_names = []
        self.field_ndims = {}
        for f in os.listdir(os.path.join(self.path, "0")):
            if f.endswith(".gz"):
                raise ValueError("Found zipped file {}. Ensure that all field files in the '0' folder are unzipped.".format(f))
            
            with open(os.path.join(self.path, "0", f), "r") as fp:
                content = fp.read()
            if "volScalarField" in content:
                self.field_names.append(f)
                self.field_ndims[f] = 1
            elif "volVectorField" in content:
                self.field_names.append(f)
                self.field_ndims[f] = 3
            else:
                self.log("Could not determine dimensionality in file %s." % (f))
        self.log("%d fields found: %s" % (len(self.field_names), ", ".join(["%s (%dD)" % (f, self.field_ndims[f]) for f in self.field_names])))

    def _read_mesh(self):
        self.mesh = Mesh(self.path)

    def add_probe(self, field, coord, name = None, color = None, coord_mode = "relative", min_distance = 0.01):
        if field not in self.field_names:
            raise ValueError("Unknown field '{}'. Available fields are: {}.".format(field, ", ".join(self.field_names)))
        new_probe = Probe(self, field, coord, name=name, color=color, coord_mode=coord_mode)
        field_probes =[p for p in self.probes if p.field == field]
        d = np.array([np.sqrt((p.coord[0] - new_probe.coord[0])**2 + (p.coord[1] - new_probe.coord[1])**2 + (p.coord[2] - new_probe.coord[2])**2) for p in field_probes])
        if len(d)==0 or min(d)>min_distance:
            self.log("Added probe at ({:.4f}, {:.4f}).".format(new_probe.coord[0], new_probe.coord[1]))
            self.probes.append(new_probe)
        else:
            imin = np.argmin(d)
            pmin = field_probes[imin]
            self.log(f"New probe is too close to existing probe {pmin.name=} of {pmin.field=} at ({pmin.coord[0]}, {pmin.coord[1]}, {pmin.coord[2]}), skipping.")

    def get_probe(self, name):
        for p in self.probes:
            if p.name == name:
                return p
        return None

    def read_probes(self, skip_first = True, tmin = -1, tmax = 100000):
        if len(self.probes) == 0:
            self.log("No probes to read.")
            return

        with TimedBlock("READING PROBES", self.log):
            for p in self.probes:
                p.t = [d for i, d in enumerate(self.time_dirs) if (self.time_vals[i] >= tmin and self.time_vals[i] <= tmax and (not skip_first or i))]
                p.data = []
    
            nt = len(self.probes[0].t)
            self.log("Using {}/{} time directories.".format(nt, len(self.time_dirs)))
            start_time = time.time()
            original_time = time.time()
            bad_dirs = []
            reasons = []
            for i, tdir in enumerate(self.probes[0].t):
                #print("\n{:>8}: ".format(tdir),)
                field_data = {}
                for p in self.probes:
                    if p.field not in field_data: # Field data has not been loaded yet, so try to load it
                        field_data[p.field] = None
                        field_path = os.path.join(self.path, tdir, p.field)
                        zipped = False
                        if not os.path.isfile(field_path): # The raw file is not there 
                            # Look for the zipped file.
                            zipped_path = field_path + ".gz"
                            if not os.path.isfile(zipped_path): # The zipped file is not there
                                bad_dirs.append(tdir)
                                msg = "Could not find raw field file {} or zipped version {}.".format(field_path, zipped_path)
                                self.log("Warning: " + msg)
                                reasons.append(msg)
                            else:
                                # Found the zipped file, unzip 
                                zipped = True
                                os.system("gunzip < {} > {}".format(zipped_path, field_path))
                                if not os.path.isfile(field_path):
                                    bad_dirs.append(tdir)
                                    msg = "Could not find {} after unziping.".format(field_path)
                                    self.log("Warning: " + msg)
                                    reasons.append(msg)

                        if tdir not in bad_dirs: # The file should be there, so try to read it:
                            field_data[p.field] = Ofpp.parse_internal_field(field_path)

                            if field_data[p.field] is None: # The file is corrupted
                                bad_dirs.append(tdir)
                                msg = "Data for field {} in time directory {} was read as None.".format(p.field, tdir)
                                self.log("Warning: " + msg)
                                reasons.append(msg)
                                
                            if zipped: # The file has been unzipped, so remove it.
                                os.system("rm {}".format(field_path))

                    # Now load the probe with data
                    if len(p.data) == 0:
                        p.data = np.zeros((nt, self.field_ndims[p.field]))

                    # If for whatever reason the time directory is unusable, set the data to Nan.
                    # Otherwise fill it with the actual data.
                    p.data[i,:] = np.nan if tdir in bad_dirs else field_data[p.field][p.index,:] if self.field_ndims[p.field]>1 else field_data[p.field][p.index]
                        
                if time.time() - start_time > 10:
                    elapsed = time.time() - original_time 
                    secs_per_timepoint = elapsed / i
                    secs_remaining = secs_per_timepoint * (nt - i)
                    self.log("Read {:>6d}/{:>6d} time points in {:>6.1f} secs. {:>6.3f} secs / time point. {:>6.3f} secs remaining). Latest directory read: {}".format(i, len(self.probes[0].t), elapsed, secs_per_timepoint, secs_remaining, tdir))
                    start_time = time.time()
            self.log("Done reading probes. {} bad time directories:".format(len(bad_dirs)))
            for i, (td, msg) in enumerate(zip(bad_dirs, reasons)):
                self.log("{:>4d}{:>12s}: {}".format(i+1, td, msg))

    def read_field(self, field, t):
        with TimedBlock("READFIELD", self.log):
            i_t = np.argmin((t - np.array(self.time_vals))**2)
            self.log("Getting field %s at time nearest to %6.3f: %6.3f." % (field, t, self.time_vals[i_t]))
            file_path = os.path.join(self.path, self.time_dirs[i_t], field)
            if not os.path.isfile(file_path):
                self.log("Could not find field file {}, trying .gz extension.".format(file_path))
                file_path += ".gz"
                if not os.path.isfile(file_path):
                    raise FileExistsError("Could not find field file {}".format(file_path))
            F = Ofpp.parse_internal_field(file_path)
        return F
        
    def snapshot_field(self, field, t, verbose = False, grid_size = 0.001, interp_method = "linear"):
        F = self.read_field(field,t)
        X = self.mesh.cell_centers[:,0]
        Y = self.mesh.cell_centers[:,1]
        DX = max(X) - min(X)
        DY = max(Y) - min(Y)
        XX, YY = np.meshgrid(np.arange(min(X), max(X), grid_size), np.arange(min(Y), max(Y), grid_size))

        ndims = self.field_ndims[field]
        FF = np.zeros((XX.shape[0], XX.shape[1], ndims ))
        if len(F.shape) == 1: #It's a vector
            F = F[:, np.newaxis] # Make it so that it's column accessible.
            
        for i in range(ndims):
            FF[:,:,i] = griddata(self.mesh.cell_centers[:,:2], F[:,i], (XX,YY), method=interp_method)

        return np.squeeze(FF), XX, YY

    def plot_field(self, field, t, vmin = None, vmax = None, probes = [], fignum=None, cmap = "jet", dim = 0, **kwargs):
        FF, XX, YY = self.snapshot_field(field, t, **kwargs);

        FF = FF if len(FF.shape)==2 else FF[:,:,dim]

        vmin = np.nanmin(FF) if not vmin else np.nanpercentile(FF,float(vmin[:-1])) if vmin[-1] == "%" else float(vmin)
        vmax = np.nanmax(FF) if not vmax else np.nanpercentile(FF,float(vmax[:-1])) if vmax[-1] == "%" else float(vmax)

        # Flip upside down so that the Y-axis labeling lines up with the data coordinates.
        plt.matshow(np.flipud(FF),extent=[np.min(XX), np.max(XX), np.min(YY), np.max(YY)], vmin = vmin, vmax = vmax, aspect="equal", fignum=fignum, cmap=eval("plt.cm."+cmap))
            
        

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--savemesh", help="Create a Mesh object from the current case and save it to file.", action="store_true")
    args = parser.parse_args()
    if args.savemesh:
        mesh = Mesh(".")
        mesh.save_to_file("mesh.p")
        print("ALLDONE")
        
        
    
    
        
