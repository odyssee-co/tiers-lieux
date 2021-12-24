import optimizer
import router
import sys
import solver


if __name__ == "__main__":
    #from IPython import embed; embed()
    nb_offices = 10
    if len(sys.argv) > 1:
        nb_offices = int(sys.argv[1])
    data_path = "/home/matt/git/tiers-lieux/data/"
    r = router.Router(data_path)
    saved_df = r.get_saved_distance()
    print("max saved distance: %s"%optimizer.eval(saved_df))
    #res = optimizer.brute_force(saved_df, nb_offices)
    #solver.solve(saved_df, nb_offices)
    #res = optimizer.random_weighted(saved_df, nb_offices, 3000)
    res = optimizer.evolutionary(saved_df, nb_offices, 0.7, 1000)
    average = 2*res[0]/(1000*saved_df.shape[0])
    print("selected offices: %s" %(res[1]))
    print("average saved distance per day and per employee: %f km"%average)
