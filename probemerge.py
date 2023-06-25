import argparse

parser = argparse.ArgumentParser(description="Merges all the probe data in the current directory into a single dataset write to the ./merged subdirectory.")
args = parser.parse_args()

import os, sys, re, pickle
import os.path as op
import numpy as np
import pdb

coords_files = []
time_files   = []
data_files   = []
for root, dirs, files in os.walk("."):
    coords_files = [op.join(root, f) for f in files if "coords.p" in f]
    times_files  = [op.join(root, f) for f in files if "t.p" in f]
    data_files   = [op.join(root, f) for f in files if "data.npy" in f]
    break

# Open the coords files and make sure they all match
print(coords_files)
coords = []
for f in coords_files:
    with open(f, "rb") as in_file:
        coords.append(pickle.load(in_file, encoding="latin1"))

for i in range(len(coords)-1):
    for j in range(i+1, len(coords)):
        if coords[i] != coords[j]:
            print("Coords in {} did not match coords in {}. Exiting.".format(coords_files[i], coords_files[j]))
            exit(1)
print("All coordinates files matched.")

times = []
for f in times_files:
    with open(f, "rb") as in_file:
        times.append(pickle.load(in_file, encoding="latin1"))

order = sorted(range(len(times)), key = lambda i: times[i][0])
print("Merge order: {}".format(order))

t = []
for i in order:
    if len(t) == 0:
        t = times[i]
        #with open(data_files[i], "rb") as in_file:
        data = np.load(data_files[i])
        print("Starting with data from {} ({:.3f} - {:.3f} sec)".format(data_files[i], t[0], t[-1]))
    else:
        for istart, tt in enumerate(times[i]):
            if tt > t[-1]:
                break
        print("Joining data from {} starting at index {}. ({:.3f} - {:.3f} sec)".format(data_files[i], istart, times[i][istart], times[i][-1]))
        new_data = np.load(data_files[i])
        t += times[i][istart:]
        data = np.concatenate((data, new_data[istart:]),axis=0)

print("Finished merging {} datasets.".format(len(order)))
d = np.diff(t)
print("Output times: {:.3f}  - {:.3f} secs. Intervals = {:.3f} +/- {:.3f} sec. (min: {:.3f}, max: {:.3f})".format(t[0], t[-1], np.mean(d), np.std(d), np.min(d), np.max(d)))
print("Data shape: {}.".format(data.shape))

print("")
os.system("mkdir -p merged")
with open("merged/probe.coords.p", "wb") as out_file:
    pickle.dump(coords[0], out_file)
    print("Wrote merged/probe.coords.p")

with open("merged/probe.t.p", "wb") as out_file:
    pickle.dump(t, out_file)
    print("Wrote merged/probe.t.p")

np.save("merged/probe.data.npy", data)
print("Wrote merged/probe.data.npy")

print("\nALLDONE.")

        
        

                     

            
    
    
    

