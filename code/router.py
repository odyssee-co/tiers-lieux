import pandas as pd
import subprocess as sp
import shutil

path = "/home/matt/git/tiers-lieux/"

def run(data_path, jar_file, requests_file, conf_file, output_file, return_flows=False):
    """
    df_requests.to_csv("%s/requests.csv" %
               context.path(), sep=";", index=False)
    read df_requests from csv
    person_id;office_id;origin_x;origin_y;destination_x;destination_y
    """

    command = [
    shutil.which("java"),
    "-cp", data_path + jar_file,
    "-Xmx14G",
    "org.eqasim.odyssee.RunBatchRouting",
    "--config-path", data_path + conf_file,
    "--input-path", data_path + requests_file,
    "--output-path", data_path + output_file
    ]

    if return_flows:
        command += [
        "--flow-output-path", "flows.csv"
        ]

    sp.check_call(command, cwd=path)

    if not return_flows:
        return pd.read_csv("%s/results.csv" % data_path, sep=";")
    else:
        return pd.read_csv("%s/flows.csv" % path, sep=";")
