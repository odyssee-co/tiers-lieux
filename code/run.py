import router
import optimizer
import os
import argparse
import visualization


if __name__ == "__main__":
    #from IPython import embed; embed()
    parser = argparse.ArgumentParser(description="Run the optimizer")
    parser.add_argument("--data_path", default="../data", help="path to the data")
    parser.add_argument("--nb_offices", "-n", type=int, default=10,
                        help="number of offices")
    parser.add_argument("--verbose", "-v", action="store_true", help="verbose mode")
    parser.add_argument("--sample", "-s", type=float, default=1, help="sample rate")
    parser.add_argument("--min", "-m", type=float, default=10000, help="Minimum saved \
                        distance for an employee to choose an office")
    parser.add_argument("--solver", type=str, help="use mip solver (glpk|cbc)")
    parser.add_argument("--show", action="store_true", help="show the data")
    parser.add_argument("--heuristic", type=str, help="use heuristic search (rand, rand_w, evol)")
    args=parser.parse_args()
    data_path = args.data_path
    nb_offices = args.nb_offices
    verbose = args.verbose
    solver = args.solver
    sample_rate = args.sample
    solver = args.solver


    processed_path = data_path+"/processed"
    if not os.path.isdir(processed_path):
        os.mkdir(processed_path)

    r = router.Router(data_path)
    saved_df = r.get_saved_distance(min_saved=args.min)
    if sample_rate < 1:
        saved_df = saved_df.sample(round(saved_df.shape[0]*sample_rate))

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
