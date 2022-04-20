import preselection
import sys
eps = int(sys.argv[1])
min_samples = int(sys.argv[2])
#top_50 = preselection.dbscan("../data/processed/Toulouse", exclude=["31555"], eps=eps, min_samples=min_samples)
top_50 = preselection.kmeans("../data/processed/Toulouse", exclude=["31555"])
print(top_50)
