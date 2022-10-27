import os, yaml

def load_muni_list(cfg):
    if "municipality_file" not in cfg.keys():
        return []
    municipalities_list = []
    municipality_file = cfg["municipality_file"]
    with open(municipality_file) as f:
        for l in f:
            municipalities_list.append(l.strip())
    return municipalities_list

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
    municipalities_list = load_muni_list(cfg)
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

    return data_path, processed_path, orig_dep, dest_dep, office_dep, departments,\
    municipalities_list, pop_src, exclude, matsim_conf, presel_functions,\
    optimizations, nb_offices, isochrones, minimals
