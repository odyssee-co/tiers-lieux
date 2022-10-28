import os, yaml

"""
def load_muni_list(cfg):
    if "muni_orig_file" not in cfg.keys():
        return []
    muni_orig = []
    muni_orig_file = cfg["muni_orig_file"]
    with open(muni_orig_file) as f:
        for l in f:
            muni_orig.append(l.strip())
    return muni_orig
"""

def parse_cfg(yml_path):
    with open(yml_path, "r") as yml_file:
        cfg = yaml.safe_load(yml_file)
    data_path = os.path.abspath(cfg["data_path"])
    processed_path = os.path.abspath(cfg["processed_path"])
    dest_dep = cfg["dest_dep"]
    if "orig_dep" in cfg.keys():
        orig_dep = cfg["orig_dep"]
        dest_dep.extend(orig_dep)
        departments = list(set(dest_dep))
    else:
        orig_dep = dest_dep
        departments = dest_dep
    if "office_dep" in cfg.keys():
        office_dep = cfg["office_dep"]
    else:
        office_dep = dest_dep

    if "muni_orig_file" not in cfg.keys():
        muni_orig = []
    else:
        muni_orig = []
        muni_orig_file = cfg["muni_orig_file"]
        with open(muni_orig_file) as f:
            for l in f:
                muni_orig.append(l.strip())


    if "office_muni_file" not in cfg.keys():
        office_muni = []
    else:
        office_muni = []
        office_muni_file = cfg["office_muni_file"]
        with open(office_muni_file) as f:
            for l in f:
                office_muni.append(l.strip())

    pop_src = cfg["pop"]
    exclude = cfg["exclude"]
    matsim_conf = os.path.abspath(cfg["matsim_conf"])
    if "preselection" in cfg.keys():
        presel_functions = cfg["preselection"]
        if type(presel_functions) != list:
            presel_functions = [presel_functions]
    else:
        presel_functions = ["all"]
    if "optimizer" in cfg.keys():
        optimizations = cfg["optimizer"]
        if type(optimizations) != list:
            optimizations = [optimizations]
    else:
        optimizations = []
    nb_offices = cfg["nb_offices"]
    if type(nb_offices) != list:
        nb_offices = [nb_offices]
    isochrones = cfg["isochrone"]
    if type(isochrones) != list:
        isochrones = [isochrones]
    minimals = cfg["min"]
    if type(minimals) != list:
        minimals = [minimals]

    return data_path, processed_path, orig_dep, dest_dep, office_dep, office_muni, \
    departments, muni_orig, pop_src, exclude, matsim_conf, presel_functions,\
    optimizations, nb_offices, isochrones, minimals
