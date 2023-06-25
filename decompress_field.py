import argparse
parser = argparse.ArgumentParser(description="Uses tar to decompress specific fields from compressed time folders into the current directory.")
parser.add_argument("field",       help="Field to decompress", type = str)
parser.add_argument("source",      help="The source folder containing the compressed data.", type=str)
parser.add_argument("--tmin",      help="Minimum time to decompress. Times >  tmin will be decompressed.",  type=float, default = 0)
parser.add_argument("--tmax",      help="Minimum time to decompress. Times <= tmax will be decompressed.",  type=float, default = 1e6)
parser.add_argument("--extension", help="The compressed file extension.", type=str, default = ".tar.gz")
parser.add_argument("--mock",      help="Whether to mock execution.", action="store_true")
args = parser.parse_args()

import os, sys
sys.path.append(os.getenv("CFDGITPY"))
import utils

tv, tf = utils.get_numerical_files(case_path = args.source, extension = args.extension)
print("Found {} total compressed files.".format(len(tv)))
use = [(tf[i], v) for i,v in enumerate(tv) if v > args.tmin and  v <= args.tmax]
print("Found {} files for the time interval ({:.3f} - {:.3f}].".format(len(use), args.tmin, args.tmax))
print("First: {:>16}".format(use[0][0]))
print(" Last: {:>16}".format(use[-1][0]))

for tfile, tval in use:    
    cmd = "tar -xvf {source_dir}/{source_file} {dir}/{field}".format(source_dir = args.source, source_file = tfile, dir=tfile[:-len(args.extension)], field=args.field)
    if not args.mock:
        print(cmd)
        os.system(cmd)
    else:
        print("mock " + cmd)
