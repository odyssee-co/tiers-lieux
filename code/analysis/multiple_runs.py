import pandas as pd
import optimizer
import router
import sys
import yaml

with open("conf.yml", "r") as yml_file:
        cfg = yaml.safe_load(yml_file)

r = router.Router(cfg)
saved_df_w = r.get_saved_distance("top_50_muni")
saved_df = saved_df_w.drop("weight", axis=1)

res_file = open(sys.argv[1], "a")

for i in range(50):
    print(i)
    res_file.write(str(optimizer.evolutionary(saved_df, 100, nb_it=400))+"\n")
res_file.close()

f=open("res.txt")
d = {}
for l in f:
    res = eval(l.strip())
    for muni in res[1]:
        if muni in d:
            d[muni] += 1
        else:
            d[muni] = 0
s = pd.Series(d, name="count")
s.index.name="commune_id"
print(list(s.sort_values(ascending=False)[:50].index))
