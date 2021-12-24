import subprocess as sp
import shutil

path = "/home/matt/git/tiers-lieux/"
jar_file = "flow-1.2.0.jar"

def run(data_path, requests_file, conf_file, output_file, return_flows=False):
    """
    read df_requests from csv and call MATSim router
    person_id;office_id;origin_x;origin_y;destination_x;destination_y
    """

    print("Routing %s..."%requests_file)

    command = [
    shutil.which("java"),
    "-cp", data_path + jar_file,
    #"-Xmx14G",
    "org.eqasim.odyssee.RunBatchRouting",
    "--config-path", data_path + conf_file,
    "--input-path", data_path + requests_file,
    "--output-path", data_path + "/processed/" + output_file
    ]

    if return_flows:
        command += [
        "--flow-output-path", "flows.csv"
        ]

    sp.check_call(command, cwd=path)
