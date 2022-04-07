def load_muni_list(cfg):
        try:
            municipalities_list = []
            municipality_file = cfg["municipality_file"]
            with open(municipality_file) as f:
                for l in f:
                    municipalities_list.append(l.strip())
            return municipalities_list
        except KeyError:
            return None
