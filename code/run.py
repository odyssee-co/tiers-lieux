#from IPython import embed; embed()
import router
import optimizer
import os
import argparse
import visualization
import preprocessing.population as pop
import preselection


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the optimizer")
    parser.add_argument("--data_path", default="../data", help="path to the data")
    parser.add_argument("--nb_offices", "-n", type=int, default=10,
                        help="number of offices")
    parser.add_argument("--verbose", "-v", action="store_true", help="verbose mode")
    parser.add_argument("--sample", "-s", type=float, default=1, help="sample rate")
    parser.add_argument("--min", "-m", type=float, default=10, help="Minimum saved \
                        time (in min) for an employee to choose an office")
    parser.add_argument("--isochrone", "-i", type=float, default=15, help="\
                        Maximum travel time (in min) for an employee to consider \
                        this office")
    parser.add_argument("--solver", type=str, help="use mip solver (glpk|cbc)")
    parser.add_argument("--pop", type=str, default="insee", help="population source (insee|hr)")
    parser.add_argument("--pre", type=str, default=None, help="preselection function")
    parser.add_argument("--show", action="store_true", help="show the data")
    parser.add_argument("--heuristic", type=str, help="use heuristic search (rand, rand_w, evol)")
    args=parser.parse_args()
    nb_offices = args.nb_offices
    data_path = os.path.abspath(args.data_path)
    verbose = args.verbose
    solver = args.solver
    sample_rate = args.sample
    solver = args.solver
    min_saved=args.min
    isochrone = args.isochrone
    pop_src = args.pop
    presel_func = args.pre

    departments = ["09", "11", "31", "32", "81", "82"]
    matsim_conf = "matsim-conf/toulouse_config.xml"
    exclude = ["31555"]


    processed_path = data_path+"/processed"
    if not os.path.isdir(processed_path):
        os.mkdir(processed_path)

    #population = pop.get_insee_population(data_path, departments)
    population = getattr(pop, f"get_{pop_src}_population")(data_path, departments)

    if presel_func:
        preselected_muni = getattr(preselection, f"{presel_func}")(data_path, exclude)
    else:
        preselected_muni = None

    #preselected_muni = preselection.get_top_50_municipalities(data_path, exclude=exclude)
    suffix = f"_iso{isochrone}_min{min_saved}_{presel_func}"
    r = router.Router(data_path, suffix, population, departments, matsim_conf, preselection=preselected_muni)
    saved_df = r.get_saved_distance(min_saved, isochrone=isochrone, min_saved=min_saved, exclude=exclude)
    if sample_rate < 1:
        saved_df = saved_df.sample(round(saved_df.shape[0]*sample_rate))


    from IPython import embed; embed()
    max = 2*optimizer.eval(saved_df)/(1000*saved_df.shape[0]) #upper bound when all offices are available
    print("nb employee: %s"%saved_df.shape[0])
    print("max saved distance per day and per employee: %.2f km\n"%max)
    #res = optimizer.exhaustive(saved_df, nb_offices)

    if args.heuristic:
        heuristic_dic = {"rand":"random", "rand_w":"random_weighted", "evol":"evolutionary"}
        heuristic = getattr(optimizer, heuristic_dic[args.heuristic])
        print("Running %s heuristic..."%heuristic_dic[args.heuristic])
        res = heuristic(saved_df, nb_offices, verbose=verbose)
        average = 2*res[0]/(1000*saved_df.shape[0])
        print("selected offices: %s" %(res[1]))
        print("average saved distance per day and per employee: %.2f km\n"%average)

    if solver:
        print("Running MIP solver...")
        res = optimizer.mip(saved_df, nb_offices, verbose=verbose, solver=solver)
        average = 2*res[0]/(1000*saved_df.shape[0])
        print("selected offices: %s" %(res[1]))
        print("average saved distance per day and per employee: %.2f km\n"%average)

    if args.show:
        visualization.viz(res)
