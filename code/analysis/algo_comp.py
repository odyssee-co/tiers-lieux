import pandas as pd
import matplotlib.pyplot as plt

plt.rcParams["figure.figsize"] = (10,6)

df = pd.read_csv("algo_comp.csv", sep=";",
    converters={"res_rw":pd.eval, "res_evo":pd.eval, "res_mip":pd.eval})
df["score_mip"] = df["res_mip"].map(lambda res: res[0])
df["accuracy_rw"] = df["res_rw"].map(lambda res: res[0]) / df["score_mip"]
df["accuracy_evo"] = df["res_evo"].map(lambda res: res[0]) / df["score_mip"]
#from IPython import embed; embed()
plt.plot(df["i"], df["score_mip"]/1e6)
plt.xlabel('Nb of shared offices')
plt.ylabel('Saved distance [1000 km]')
plt.grid()
plt.savefig("distance.png")
plt.show()

plt.plot(df["i"], df["accuracy_evo"], color="orange", label="evolutionary")
plt.plot(df["i"], df["accuracy_rw"], color="green", label="random_weighted")
plt.xlabel('Nb of shared offices')
plt.ylabel('Accuracy')
plt.legend()
plt.grid()
plt.savefig("accuracy.png")
plt.show()

plt.plot(df["i"], df["time_mip"], label="cbc_solver")
plt.plot(df["i"], df["time_evo"], color="orange", label="evolutionary")
plt.plot(df["i"], df["time_rw"], color="green", label="random_weighted")
plt.xlabel('Nb of shared offices')
plt.ylabel('Time (s)')
plt.legend()
plt.grid()
plt.savefig("times.png")
plt.show()

plt.plot(df["i"], df["time_evo"], color="orange", label="evolutionary")
plt.plot(df["i"], df["time_rw"], color="green", label="random_weighted")
plt.xlabel('Nb of shared offices')
plt.ylabel('Time (s)')
plt.legend()
plt.grid()
plt.savefig("times_heuri.png")
plt.show()
