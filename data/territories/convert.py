import sys
path = sys.argv[1]
with open(path) as r:
    with open(f"{path[:-4]}_insee.txt", "w") as w:
        for l in r:
            line = l.strip()[-6:-1]
            w.write(f"{line}\n")
