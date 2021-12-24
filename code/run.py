import preprocessing.requests as req
import pandas as pd
import os
import router
import optimizer
import solver


def get_routed_initial():
    """
    return a dataframe with the travel time for each employee to his original office
    "office_id", "car_travel_time", "car_distance", "pt_travel_time", "pt_distance"
    """
    routed_initial_path = "%s/processed/routed_initial.csv"%data_path
    if not os.path.isfile(routed_initial_path):
        req.compute_initial_requests(data_path)
        router.run(data_path, "/processed/initial_request.csv",
                "/matsim-conf/toulouse_config.xml", "routed_initial.csv")
    return pd.read_csv(routed_initial_path, sep=";")


def get_routed_office():
    """
    return a dataframe with the travel time for each employees to each office
    "office_id", "car_travel_time", "car_distance", "pt_travel_time", "pt_distance"
    """
    routed_offices_path = "%s/processed/routed_offices.csv"%data_path
    if not os.path.isfile(routed_offices_path):
        req.compute_offices_request(data_path)
        router.run(data_path, "/processed/offices_request.csv",
                "/matsim-conf/toulouse_config.xml", "routed_offices.csv")
    return pd.read_csv(routed_offices_path, sep=";")


def get_saved_distance():
    """
    return a dataframe containing for each employee, the time he would save working
    in each office (0 if the saved time if negative)
    """
    routed_inital = get_routed_initial()
    routed_offices = get_routed_office()
    routed_inital = routed_inital.rename(columns={
        "office_id" : "original_office",
        "car_travel_time" : "baseline_car_travel_time",
        "car_distance" : "baseline_car_distance",
        "pt_travel_time" : "baseline_pt_travel_time",
        "pt_distance" : "baseline_pt_distance",
    })
    df = pd.merge(routed_inital, routed_offices, on="person_id", how="left")
    df["saved_travel_distance"] = df["baseline_car_distance"] - df["car_distance"]
    saved_df = df.pivot(index="person_id", columns="office_id", values="saved_travel_distance")
    saved_df = saved_df.where(saved_df > 0, 0)
    return saved_df


if __name__ == "__main__":
    #from IPython import embed; embed()
    nb_offices = 3
    data_path = "/home/matt/git/tiers-lieux/data/"
    #offices_file = "top50.txt"
    saved_df = get_saved_distance()
    #res = optimizer.brute_force(saved_df, nb_offices)
    #print("max saved distance: %s"%optimizer.eval(saved_df))
    #res = optimizer.random_weighted(saved_df, nb_offices, 3000)
    #res = optimizer.evolutionary(saved_df, nb_offices, 0.7, 1000)
    solver.solve(saved_df, nb_offices)
    """
    print("selected offices: %s" %(res[1]))
    print("average saved distance: %f km" %(2*res[0]/(1000*saved_df.shape[0])))
    """
