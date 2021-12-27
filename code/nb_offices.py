import router
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

    out = []
    for i in range(1, int(saved_df.shape[1]/2)):
        res = optimizer.evolutionary(saved_df, i+1, nb_it=200)
        average = 2*res[0]/(1000*saved_df.shape[0])
        out.append(average)

    with open(output_path, "w") as f:
        for e in out:
            f.write(str(e)+"\n")
    pyplot.plot(range(2, len(out)+2),out)
    pyplot.xlabel('nb_tierslieux')
    pyplot.ylabel('saved_distance_per_employee_per_day (km)')
    pyplot.show() 
