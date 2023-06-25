import os, sys
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("num_sources", help="The number of sources.", type = int)
parser.add_argument("ymin", help="The minimum center of a source.", type = float)
parser.add_argument("ymax", help="The maximum center of a source.", type = float)
parser.add_argument("width", help="The source width.", type = float)
args = parser.parse_args()
print(args)


def roundn(x, n):
    return round(x*10**n)/10**n

ymin  = args.ymin
ymax  = args.ymax
width = args.width
num_sources = args.num_sources
centers = [ymin + (ymax - ymin)/(num_sources - 1)*i for i in range(num_sources)]
ranges  = [(roundn(c-width/2,3), roundn(c + width/2,3)) for c in centers]
print(centers)
print(ranges)

if not os.path.isfile("S0"):
    print("Could not find S0 in current directory. Exiting.")
    exit(1)
    
for i, (ymin, ymax) in enumerate(ranges):
    cmd = 'sed s/S0/S{}/g S0 > S{}; sed -i s/YMIN/{}/g S{}; sed -i s/YMAX/{}/g S{};'.format(i+1, i+1, ymin, i+1, ymax, i+1)    
    print(cmd)
    os.system(cmd)
