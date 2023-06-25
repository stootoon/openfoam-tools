import os, sys
import shutil
from glob import glob
import boulder
import imageio
from matplotlib.pyplot import imsave
from tqdm import tqdm
from argparse import ArgumentParser


parser = ArgumentParser()
parser.add_argument("zip1", type=str, help="First zip file.")
parser.add_argument("zip2", type=str, help="Second zip file.")
parser.add_argument("--framerate", type=int, help="Frame rate.", default=100)
parser.add_argument("--quality", type=int, help="Quality. 1-31, lower is better.", default=1)
args = parser.parse_args()

zip1 = args.zip1
zip2 = args.zip2
quality = args.quality
framerate = args.framerate

os.system("rm -rf tmp1 tmp2")

print(f"Unpacking {zip1} to tmp1...")
shutil.unpack_archive(zip1, extract_dir = "tmp1")
print(f"Unpacking {zip2} to tmp2...")
shutil.unpack_archive(zip2, extract_dir = "tmp2")

dir_names = [f"tmp{i+1}/"+z.split("/")[-1][:-7] for i,z in enumerate([zip1, zip2])]
print(f"Content directories: ")
print(dir_names)


files = [sorted(glob(d + "/*.png")) for d in dir_names]
for d, f in zip(dir_names, files):
    print(f"Found {len(f)} files in {d}.")

base_names = [[os.path.basename(f) for f in fi] for fi in files]
if len(set(base_names[0]) - set(base_names[1]))!=0:
    print("Warning: Some files found in {} that don't exist in {}: {}".format(dir_names[0], dir_names[1], set(base_names[0]) - set(base_names[1])))

if len(set(base_names[1]) - set(base_names[0]))!=0:
    print("Warning: Some files found in {} that don't exist in {}: {}".format(dir_names[1], dir_names[0], set(base_names[1]) - set(base_names[0])))

common_base_names = sorted(list(set(base_names[0]).intersection(base_names[1])))
assert len(common_base_names), "No files found with common base names."
print(f"Using the {len(common_base_names)} with common base names.")

os.system("rm -rf comb; mkdir comb")
print("Combining pngs.")
for i, bn in tqdm(enumerate(common_base_names)):
    f0 = os.path.join(dir_names[0], bn)
    f1 = os.path.join(dir_names[1], bn)
    im0 = imageio.imread(f0)
    im1 = imageio.imread(f1)
    rgb = boulder.combine_plume_images(im0[:,:,0]/255, im1[:,:,0]/255)
    imsave(f"comb/{i:05d}.png", (rgb*255).astype("uint8"))
print("")
print("Writing comb.avi")
cmd = f'ml FFmpeg; ffmpeg -r {framerate} -pattern_type glob -i "comb/*.png" -vcodec mpeg4 -qscale:v {quality} comb.avi'
print(cmd)
os.system(cmd)
print("ALLDONE.")
