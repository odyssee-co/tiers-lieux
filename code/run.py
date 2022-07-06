#from IPython import embed; embed()
import router
import optimizer
import os
import argparse
import preprocessing.communes as com
import preprocessing.population as pop
import yaml
import utils
import pandas as pd
import geopandas as gpd
from itertools import product


def optimize(opt_func, n, iso, min, presel):
    res_path = f"{processed_path}/res.csv"
    if not os.path.exists(res_path):
        with open(res_path, "w") as f:
            f.write("n;iso;min;presel;optimizer;saved_d;selected_muni\n")
    r = pd.read_csv(res_path, sep=";")
    res = r[(r["optimizer"]==opt_func) & (r["n"]==n) & (r["iso"]==iso) & (r["min"]==min)]
    if len(res) > 0:
        res = [res.iloc[0].saved_d, eval(res.iloc[0].selected_muni)]
    else:
        opt = getattr(optimizer, opt_func)
        print(f"Optimizing ({n},{iso},{min},{presel},{opt_func})...")
        res = opt(saved_df, n, verbose=verbose)
        with open(res_path, "a") as f:
            f.write(f"{n};{iso};{min};{presel};{opt_func};{res[0]};{res[1]}\n")
    if verbose:
        average = 2*res[0]/(1000*nb_employees)
        print("selected offices: %s" %(res[1]))
        print("average saved distance per day and per employee: %.2f km\n"%average)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the optimizer")
    parser.add_argument("--conf", default="conf.yml", help="path to the configuraiton file")
    parser.add_argument("--verbose", "-v", action="store_true", help="verbose mode")
    parser.add_argument("--interactive", "-i", action="store_true", help="interactive mode")
    parser.add_argument("--sample", "-s", type=float, default=1, help="sample rate")

    args=parser.parse_args()
    yml_path = args.conf
    verbose = args.verbose
    sample_rate = args.sample

    with open(yml_path, "r") as yml_file:
        cfg = yaml.safe_load(yml_file)
    data_path = os.path.abspath(cfg["data_path"])
    processed_path = os.path.abspath(cfg["processed_path"])
    dest_dep = cfg["dest_dep"]
    if "orig_dep" in cfg.keys():
        orig_dep = cfg["orig_dep"]
        dest_dep.extend(orig_dep)
        departments = list(set(dest_dep))
    else:
        orig_dep = dest_dep
        departments = dest_dep

    municipalities_list = utils.load_muni_list(cfg)

    if not os.path.isdir(processed_path):
        os.mkdir(processed_path)

    communes_path = f"{processed_path}/communes.gpkg"
    if not os.path.isfile(communes_path):
        df_communes = com.get_communes(data_path, municipalities=municipalities_list,
                                       departments=departments)
        df_communes.to_file(communes_path, driver = "GPKG")
    df_communes = gpd.read_file(communes_path, dtype={"commune_id":str})
    zone = df_communes[df_communes.commune_id.str[:2].isin(orig_dep)]
    zone_center = zone.dissolve().centroid.iloc[0]
    print(f"zone center: {zone_center.x}, {zone_center.y}")

    pop_path = f"{processed_path}/persons.feather"
    if not os.path.isfile(pop_path):
        pop_src = cfg["pop"]
        df_pop = getattr(pop, f"get_{pop_src}_population")(data_path,
                    orig_dep=orig_dep, dest_dep=dest_dep, municipalities=municipalities_list)
        df_pop.reset_index(drop=True).to_feather(pop_path)
    df_pop = pd.read_feather(pop_path)

    exclude = cfg["exclude"]
    matsim_conf = os.path.abspath(cfg["matsim_conf"])
    r = router.Router(data_path, processed_path, exclude, matsim_conf)

    if "preselection" in cfg.keys():
        presel_functions = cfg["preselection"]
        if type(presel_functions) != list:
            presel_functions = [presel_functions]
    else:
        presel_functions = [None]

    if "optimizer" in cfg.keys():
        optimizations = cfg["optimizer"]
        if type(optimizations) != list:
            optimizations = [optimizations]
    else:
        optimizations = []

    nb_offices = cfg["nb_offices"]
    if type(nb_offices) != list:
        nb_offices = [nb_offices]

    isochrones = cfg["isochrone"]
    if type(isochrones) != list:
        isochrones = [isochrones]

    minimals = cfg["min"]
    if type(minimals) != list:
        minimals = [minimals]

    for iso, min, presel in product(isochrones, minimals, presel_functions):
        saved_df_w = r.get_saved_distance(iso, min, presel)
        if sample_rate < 1:
            saved_df_w = saved_df_w.sample(round(saved_df_w.shape[0]*sample_rate))
        saved_df = saved_df_w.drop("weight", axis=1)
        if verbose:
            nb_employees = saved_df_w.weight.sum()
            max = 2*optimizer.eval(saved_df)/(1000*nb_employees) #upper bound when all offices are available
            print("nb employee: %s"%nb_employees)
            print("max saved distance per day and per employee: %.2f km\n"%max)
        if len(optimizations) > 0:
            for opt, n in product(optimizations, nb_offices):
                optimize(opt, n, iso, min, presel)

    if args.interactive:
        from IPython import embed; embed()
