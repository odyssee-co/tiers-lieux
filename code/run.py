import router
import optimizer
import os
import argparse


if __name__ == "__main__":
    #from IPython import embed; embed()
    parser = argparse.ArgumentParser(description='Run the optimizer')
    parser.add_argument('data_path', help='path to the data')
    parser.add_argument('--nb_offices', "-n", type=int, default=10,
                        help='number of offices')
    parser.add_argument('--verbose', "-v", action="store_true", help='verbose mode')
    args=parser.parse_args()
    data_path = args.data_path
    nb_offices = args.nb_offices
    verbose = args.verbose

    processed_path = data_path+"/processed"
    if not os.path.isdir(processed_path):
        os.mkdir(processed_path)

    r = router.Router(data_path)
    saved_df = r.get_saved_distance()
    saved_df = saved_df.iloc[:500,:]
    print("max saved distance: %s\n"%optimizer.eval(saved_df)) #upper bound when all offices are available
    #res = optimizer.exhaustive(saved_df, nb_offices)

    print("Running evolutionary heuristic...")
    res = optimizer.evolutionary(saved_df, nb_offices, verbose)
    average = 2*res[0]/(1000*saved_df.shape[0])
    print("selected offices: %s" %(res[1]))
    print("average saved distance per day and per employee: %f km\n"%average)

    print("Running MIP solver...")
    res = optimizer.mip(saved_df, nb_offices)
    average = 2*res[0]/(1000*saved_df.shape[0])
    print("selected offices: %s" %(res[1]))
    print("average saved distance per day and per employee: %f km\n"%average)
