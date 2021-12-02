import preprocessing.process_hr as hr
import preprocessing.communes as com
import router

data_path = "/home/matt/git/tiers-lieux/data"

if __name__ == "__main__":
    #from IPython import embed; embed()
    communes = com.get_communes(data_path)
    print(communes)
    hr_df = hr.process_action_logement(data_path, communes)
    print(hr_df)
    reg_df = hr.process_region(data_path)
    print(reg_df)
    met_df = hr.process_metropole(data_path)
    print(met_df)
    """
    person_id;office_id;origin_x;origin_y;destination_x;destination_y
    router.run()
    """
