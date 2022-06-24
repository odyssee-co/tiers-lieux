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

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the optimizer")
    parser.add_argument("--conf", default="conf.yml", help="path to the configuraiton file")
    parser.add_argument("--verbose", "-v", action="store_true", help="verbose mode")
    parser.add_argument("--interactive", "-i", action="store_true", help="interactive mode")
    parser.add_argument("--nb_offices", "-n", type=int, default=10,
                        help="number of offices")
    parser.add_argument("--sample", "-s", type=float, default=1, help="sample rate")
    parser.add_argument("--solver", type=str, help="use mip solver (glpk|cbc)")
    parser.add_argument("--heuristic", type=str, help="use heuristic search (rand, rand_w, evol)")

    args=parser.parse_args()
    yml_path = args.conf
    verbose = args.verbose
    nb_offices = args.nb_offices
    sample_rate = args.sample
    solver = args.solver

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

    presel_func = None
    if "preselection" in cfg.keys():
        presel_func = cfg["preselection"]

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

    r = router.Router(cfg)
    saved_df_w = r.get_saved_distance(presel_func)

    if sample_rate < 1:
        saved_df_w = saved_df_w.sample(round(saved_df_w.shape[0]*sample_rate))
    saved_df = saved_df_w.drop("weight", axis=1)

    nb_employees = saved_df_w.weight.sum()
    max = 2*optimizer.eval(saved_df)/(1000*nb_employees) #upper bound when all offices are available
    print("nb employee: %s"%nb_employees)
    print("max saved distance per day and per employee: %.2f km\n"%max)
    #res = optimizer.exhaustive(saved_df, nb_offices)

    if args.heuristic:
        heuristic_dic = {"rand":"random", "rand_w":"random_weighted", "evol":"evolutionary"}
        heuristic = getattr(optimizer, heuristic_dic[args.heuristic])
        print("Running %s heuristic..."%heuristic_dic[args.heuristic])
        res = heuristic(saved_df, nb_offices, verbose=verbose)
        average = 2*res[0]/(1000*nb_employees)
        print("selected offices: %s" %(res[1]))
        print("average saved distance per day and per employee: %.2f km\n"%average)

    if solver:
        solver_res_path = f"{processed_path}/solver_res_iso{cfg['isochrone']}.txt"
        print("Running MIP solver...")
        res = optimizer.mip(saved_df, nb_offices, verbose=verbose, solver=solver)
        with open(solver_res_path, "a") as f:
            f.write(f"{res}\n")
        average = 2*res[0]/(1000*nb_employees)
        print("selected offices: %s" %(res[1]))
        print("average saved distance per day and per employee: %.2f km\n"%average)

    if args.interactive:
        from IPython import embed; embed()
