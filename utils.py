import os, sys, time, re
from datetime import datetime

class TimedBlock():
    def __init__(self, name, printfun = lambda x: sys.stdout.write(x+"\n") ):
        self.name = name
        self.printfun = printfun

    def __enter__(self):
        self.printfun("{}: Started {}.".format(datetime.now(), self.name))
        self.start_time = time.time()

    def __exit__(self, *args):
        self.printfun("{}: Finished {} in {} seconds.".format(datetime.now(), self.name, time.time() - self.start_time))

def argsort(seq):
    #http://stackoverflow.com/questions/3382352/equivalent-of-numpy-argsort-in-basic-python/3382369#3382369
    #by unutbu
    return sorted(range(len(seq)), key=seq.__getitem__)

def get_numerical_directories(case_path = "."):
    dirs = next(os.walk(case_path))[1]    
    time_dirs = [d for d in dirs if re.match("[0-9]+\.?[0-9]*", d)]
    time_vals = [float(d) for d in time_dirs]
    ind = argsort(time_vals)
    time_vals = [time_vals[i] for i in ind]
    time_dirs = [time_dirs[i] for i in ind]
    return time_vals, time_dirs

def get_numerical_files(case_path = ".", extension = ".tar.gz"):
    files = next(os.walk(case_path))[2]    
    time_files = [f for f in files if re.match("[0-9]+\.?[0-9]*", f) and f.endswith(extension)]
    time_vals = [float(f[:-len(extension)]) for f in time_files]
    ind = argsort(time_vals)
    time_vals  = [time_vals[i] for i in ind]
    time_files = [time_files[i] for i in ind]
    return time_vals, time_files
    
