import router
import optimizer
import solver
import sys, os
import argparse


if __name__ == "__main__":
    #from IPython import embed; embed()
    parser = argparse.ArgumentParser(description='Run the optimizer')
    parser.add_argument('data_path', help='path to the data')
    parser.add_argument('--nb_offices', "-n", type=int, default=10,
                        help='number of offices')
    args=parser.parse_args()
    data_path = args.data_path
    nb_offices = args.nb_offices

    processed_path = data_path+"/processed"
    if not os.path.isdir(processed_path):
        os.mkdir(processed_path)

    r = router.Router(data_path)
    saved_df = r.get_saved_distance()
    print("max saved distance: %s"%optimizer.eval(saved_df)) #upper bound when all offices are available

    #res = optimizer.brute_force(saved_df, nb_offices)
    #solver.solve(saved_df, nb_offices)
    #res = optimizer.random_weighted(saved_df, nb_offices)
    res = optimizer.evolutionary(saved_df, nb_offices)
    average = 2*res[0]/(1000*saved_df.shape[0])
    print("selected offices: %s" %(res[1]))
    print("average saved distance per day and per employee: %f km"%average)
