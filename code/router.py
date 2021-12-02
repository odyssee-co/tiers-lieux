import pandas as pd
import subprocess as sp
import shutil

def run(df_requests, return_flows=False):
    """
    df_requests.to_csv("%s/requests.csv" %
               context.path(), sep=";", index=False)
    read df_requests from csv
    person_id;office_id;origin_x;origin_y;destination_x;destination_y
    """

    command = [
    shutil.which(context.config("java_path")),
    "-cp", "%s/%s" % (context.config("data_path"),
                  context.config("jar_path")),
    "-Xmx%s" % context.config("java_memory"),
    "org.eqasim.odyssee.RunBatchRouting",
    "--config-path", "%s/%s" % (context.config("data_path"),
                            context.config("scenario_config_path")),
    "--input-path", "requests.csv",
    "--output-path", "results.csv"
    ]

    travel_times_path = context.config("travel_times_path")

    if not travel_times_path == "undefined":
        command += [
        "--update-network-path", "%s/%s" % (
            context.config("data_path"), travel_times_path),
        "--minimum-speed", "3.4"
        ]

    if return_flows:
        command += [
        "--flow-output-path", "flows.csv"
        ]

    sp.check_call(command, cwd=context.path())

    if not return_flows:
        return pd.read_csv("%s/results.csv" % context.path(), sep=";")
    else:
        return pd.read_csv("%s/flows.csv" % context.path(), sep=";")
