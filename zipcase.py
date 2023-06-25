import os, sys, time, datetime
sys.path.append(os.getenv("CFDGITPY"))
import utils as utils

os.system("mkdir _case")
_, dirs   = utils.get_numerical_directories(case_path = ".")
dirs += ["system", "constant"]
files = ["foam.foam", "*.msh"]

print "Copying {} directories.".format(len(dirs))
start_time = time.time()
for i,d in enumerate(dirs):
    os.system("cp -R {} _case".format(d))
    print ".",
    if (i % 10) == 9:
        elapsed = time.time() - start_time
        unit_time = elapsed / (i+1)
        remaining = (len(dirs) - (i+1))*unit_time
        print " {:>5}/{:<5} ({:6.3f} secs / dir). {:6.1f} secs elapsed, {:6.1f} secs remaining.".format(i+1, len(dirs), unit_time, elapsed, remaining)
    sys.stdout.flush()

print "Copying files."
for f in files:
    os.system("cp {} _case".format(f))

print "ALLDONE."

