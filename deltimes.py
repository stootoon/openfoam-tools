import os, sys, re

if len(sys.argv) < 2:
    print("Recursively deletes all time folders in this directory or below for times AFTER the specified time.")
    print("Usage: python deltimes.py [time]")
    exit(1)

after = float(sys.argv[1])
print("Deleting all time folders after {}".format(after))
for root, dirs, files in os.walk(".", topdown=False):
    for name in dirs:
        if re.match("/?[0-9]+\.?[0-9]*$", name):
            if float(name) > after:
                full = os.path.join(root, name)
                print("Deleting {}".format(full))
                os.system("rm -rf {}".format(full))
print("Done.")
