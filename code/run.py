import preprocessing.process_hr as hr
import preprocessing.communes as com

data_path = "/home/matt/git/third-place/data"

if __name__ == "__main__":
    communes = com.get_communes(data_path)
    """
    hr_df = hr.process_action_logement(data_path)
    print(hr_df)
    reg_df = hr.process_region(data_path)
    print(reg_df)
    met_df = hr.process_metropole(data_path)
    print(met_df)
    """
