import pandas as pd
import matplotlib.pyplot as plt

plt.rcParams["figure.figsize"] = (10,6)

df = pd.read_csv("algo_comp.csv", sep=";",
    converters={"res_rw":pd.eval, "res_evo":pd.eval, "res_mip":pd.eval})
df["accuracy_rw"] = df["res_rw"].map(lambda res: res[0]) / df["res_mip"].map(lambda res: res[0])
df["accuracy_evo"] = df["res_evo"].map(lambda res: res[0]) / df["res_mip"].map(lambda res: res[0])
#from IPython import embed; embed()
plt.plot(df["i"], df["accuracy_rw"], label="random_weighted")
plt.plot(df["i"], df["accuracy_evo"], label="evolutionary")
plt.xlabel('Nb of shared offices')
plt.ylabel('Accuracy')
plt.legend()
plt.grid()
plt.show()

plt.plot(df["i"], df["time_mip"], label="time_mip")
plt.plot(df["i"], df["time_evo"], label="time_evo")
plt.plot(df["i"], df["time_rw"], label="time_rw")
plt.xlabel('Nb of shared offices')
plt.ylabel('Time (s)')
plt.legend()
plt.grid()
plt.show()

plt.plot(df["i"], df["time_evo"], label="time_evo")
plt.plot(df["i"], df["time_rw"], label="time_rw")
plt.xlabel('Nb of shared offices')
plt.ylabel('Time (s)')
plt.legend()
plt.grid()
plt.show()
