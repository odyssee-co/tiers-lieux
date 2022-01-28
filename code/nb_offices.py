import router
import time
import argparse
import optimizer
from matplotlib import pyplot

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Run the optimizer')
    parser.add_argument('data_path', help='path to the data')
    parser.add_argument('--out', default="out.txt", help='output path')
    args=parser.parse_args()
    data_path = args.data_path
    output_path = args.out
    r = router.Router(data_path)
    saved_df = r.get_saved_distance()
    #saved_df = saved_df.sample(round(saved_df.shape[0]*0.01))

    with open(output_path, "w") as f:
        f.write("i;time_mip;res_mip;time_rw;res_rw;time_evo;res_evo\n")
        for i in range(2, int(saved_df.shape[1]/2)):
            print(i, flush=True)
            begin = time.time()
            res_mip = optimizer.mip(saved_df, i, solver="cbc")
            time_mip = time.time() - begin
            begin = time.time()
            res_rw = optimizer.random_weighted(saved_df, i)
            time_rw = time.time() - begin
            begin = time.time()
            res_evo = optimizer.evolutionary(saved_df, i)
            time_evo = time.time() - begin
            f.write(f"{i};{time_mip};{res_mip};{time_rw};{res_rw};{time_evo};{res_evo}\n")
            f.flush()
    """
    pyplot.plot(range(2, len(out)+2),out)
    pyplot.xlabel('nb_tierslieux')
    pyplot.ylabel('saved_distance_per_employee_per_day (km)')
    pyplot.show() 
    """
