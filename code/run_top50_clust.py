import preselection
import sys
eps = int(sys.argv[1])
min_samples = int(sys.argv[2])
preselection.top_50_clusters("../data/processed/Toulouse", eps=eps, min_samples=min_samples)
