import argparse
import utils

parser = argparse.ArgumentParser(description="Lists the time directories for the OpenFOAM case in the specified directory.")
parser.add_argument("--source", help="Directory containing the case files.", type=str, default=".")
parser.add_argument("--tmin",   help="Minimum time to list.", type=float, default=0)
parser.add_argument("--tmax",   help="Maximum time to list.", type=float, default=10000)
args = parser.parse_args()

time_vals, time_dirs = utils.get_numerical_directories(case_path = args.source)
tdirs = [td for i, td in enumerate(time_dirs) if time_vals[i] >= args.tmin and time_vals[i] <= args.tmax]
print("\n".join(tdirs))

