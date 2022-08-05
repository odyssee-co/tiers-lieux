import pandas as pd
import matplotlib.pyplot as plt

r = pd.read_csv("~/git/tiers-lieux/data/processed/Toulouse/res.csv", sep=";").iloc[:,:-1]
r = r.sort_values(by="saved_d", ascending=False)
r = r.sort_values(by=["n", "iso"])
r.saved_d*=2

mip15 = r[(r.optimizer=="mip")&(r.iso==30)]
df = mip15[mip15.presel=="top_50"]
plt.plot(df.n, df.saved_d/1e9, label="top_50")
df = mip15[mip15.presel=="dbscan"]
plt.plot(df.n, df.saved_d/1e9, label="dbscan")
df = mip15[mip15.presel=="kmeans"]
plt.plot(df.n, df.saved_d/1e9, label="kmeans")
df = mip15[mip15.presel=="kde"]
plt.plot(df.n, df.saved_d/1e9, label="kde")
plt.legend()
plt.xlabel('Number of selected offices $n$')
plt.ylabel('Saved distance (Mio km)')
plt.grid()
plt.show()

for iso in [15, 30 , 60]:
    df = r[(r.presel=="all")&(r.iso==iso)&(r.optimizer=="p_evolutionary")]
    plt.plot(df.n, df.saved_d/1e9, label="evolutionary")
    df = r[(r.presel=="all")&(r.iso==iso)&(r.optimizer=="random_weighted")]
    plt.plot(df.n, df.saved_d/1e9, label="random_weighted")
    df = r[(r.presel=="top_50")&(r.iso==iso)&(r.optimizer=="mip")]
    plt.plot(df.n, df.saved_d/1e9, label="cbc")
    plt.legend()
    plt.xlabel('Number of selected offices $n$')
    plt.ylabel('Saved distance (Mio km)')
    plt.axis((None,None,None,8))
    plt.grid()
    plt.show()

"""
for iso in [15, 30 , 60]:
    df = r[(r.presel=="all")&(r.iso==iso)&(r.optimizer=="p_evolutionary")]
    plt.plot(df.n, df.exec_time, label="evolutionary")
    df = r[(r.presel=="all")&(r.iso==iso)&(r.optimizer=="random_weighted")]
    plt.plot(df.n, df.exec_time, label="random_weighted")
    df = r[(r.presel=="top_50")&(r.iso==iso)&(r.optimizer=="mip")]
    plt.plot(df.n, df.exec_time, label="cbc")
    plt.legend()
    plt.xlabel('Number of selected offices $n$')
    plt.ylabel('Execution time (s)')
    plt.show()
"""
#from IPython import embed; embed()
