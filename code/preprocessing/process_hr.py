import pandas as pd
import numpy as np
import preprocessing.communes as com
import os


def process_action_logement(data_path, communes):
    # Fichier 1
    df_names = com.get_insee_name(data_path)
    df_conversion = com.get_insee_postal(data_path)
    df1 = pd.read_excel(data_path+"/workers_hr/Fichier 1.xlsx")

    df1 = df1.rename(columns={
        "Commune Adresse de résidence": "origin_name",
        "Lieu de travail": "destination_name"
    })
    df1["origin_name"] = df1["origin_name"].str.upper()
    df1["destination_name"] = df1["destination_name"].str.upper()
    df1 = pd.merge(df1,
                   df_names.rename(
                       columns={"office_id": "origin_id", "label": "origin_name"}),
                   on="origin_name", how="left"
                   )
    df1 = pd.merge(df1,
                   df_names.rename(
                       columns={"office_id": "destination_id", "label": "destination_name"}),
                   on="destination_name", how="left"
                   )

    df1 = df1[["origin_id", "destination_id", "origin_name", "destination_name"]]
    df1["file"] = 1

    # Fichier 2

    df2 = pd.read_excel(data_path+"/workers_hr/Fichier 2.xls")

    df2 = df2.rename(columns={
        "BG_VilledeResidence": "origin_name",
        "BG_VilledeTravail": "destination_name"
    })

    df2["origin_name"] = df2["origin_name"].str.upper()
    df2["destination_name"] = df2["destination_name"].str.upper()

    df2 = pd.merge(df2,
                   df_names.rename(
                       columns={"office_id": "origin_id", "label": "origin_name"}),
                   on="origin_name", how="left"
                   )

    #df2 = pd.merge(df2,
    #    df_names.rename(columns = { "office_id": "destination_id", "label": "destination_name" }),
    #    on = "destination_name", how = "left"
    #)

    df2["destination_name"] = "LABEGE"
    df2["destination_id"] = 31254

    #df2.loc[df2["destination_name"] == "LABEGE", "destination_id"]=31254]
    df2.loc[df2["origin_name"] == "LABEGE", "origin_id"] = 31254

    df2 = df2[["origin_id", "destination_id", "origin_name", "destination_name"]]
    df2["file"] = 2

    # Fichier 3

    df3 = pd.read_excel(data_path+"/workers_hr/Fichier 3.xls", skiprows=[1])

    df3 = df3.rename(columns={
        "Ville1-Résidence": "origin_id",
        "Ville2-Travail": "destination_id"
    })

    df3["origin_id"] = df3["origin_id"].astype(str)
    df3["destination_id"] = df3["destination_id"].astype(str)

    df3 = pd.merge(df3,
                   df_names.rename(
                       columns={"office_id": "origin_id", "label": "origin_name"}),
                   on="origin_id", how="left"
                   )

    df3 = pd.merge(df3,
                   df_names.rename(
                       columns={"office_id": "destination_id", "label": "destination_name"}),
                   on="destination_id", how="left"
                   )

    df3 = df3[["origin_id", "destination_id", "origin_name", "destination_name"]]
    df3["file"] = 3

    # Fichier 4

    df4 = pd.read_excel(data_path+"/workers_hr/Fichier 4.xlsx", skiprows=[1])

    df4 = df4.rename(columns={
        "Ville1-Résidence": "origin_postal_id",
        "Ville2-Travail": "destination_postal_id"
    })

    df4["origin_postal_id"] = df4["origin_postal_id"].astype(str)
    df4["destination_postal_id"] = df4["destination_postal_id"].astype(str)

    df4 = pd.merge(df4,
                   df_conversion.rename(
                       columns={"commune_id": "origin_id", "postal_id": "origin_postal_id"}),
                   on="origin_postal_id", how="left"
                   )

    df4 = pd.merge(df4,
                   df_names.rename(
                       columns={"office_id": "origin_id", "label": "origin_name"}),
                   on="origin_id", how="left"
                   )

    df4 = pd.merge(df4,
                   df_conversion.rename(
                       columns={"commune_id": "destination_id", "postal_id": "destination_postal_id"}),
                   on="destination_postal_id", how="left"
                   )

    df4 = pd.merge(df4,
                   df_names.rename(
                       columns={"office_id": "destination_id", "label": "destination_name"}),
                   on="destination_id", how="left"
                   )

    #df4 = pd.merge(df4,
    #    df_names.rename(columns = { "office_id": "origin_id", "label": "origin_name" }),
    #    on = "origin_id", how = "left"
    #)

    #df4 = pd.merge(df4,
    #    df_names.rename(columns = { "office_id": "destination_id", "label": "destination_name" }),
    #    on = "destination_id", how = "left"
    #)

    df4 = df4[["origin_id", "destination_id", "origin_name", "destination_name"]]
    df4["file"] = 4

    # Fichier 5

    df5 = pd.read_excel(data_path+"/workers_hr/Fichier 5.XLSX")

    df5 = df5.rename(columns={
        "Code postal Ville de Résidence": "origin_postal_id",
        "Lieu de travail": "destination_name"
    })

    df5["origin_postal_id"] = df5["origin_postal_id"].astype(str)
    df5["destination_name"] = df5["destination_name"].str.upper()

    df5 = pd.merge(df5,
                   df_conversion.rename(
                       columns={"commune_id": "origin_id", "postal_id": "origin_postal_id"}),
                   on="origin_postal_id", how="left"
                   )

    df5 = pd.merge(df5,
                   df_names.rename(
                       columns={"office_id": "origin_id", "label": "origin_name"}),
                   on="origin_id", how="left"
                   )

    df5 = pd.merge(df5,
                   df_names.rename(
                       columns={"office_id": "destination_id", "label": "destination_name"}),
                   on="destination_name", how="left"
                   )

    df5 = df5[["origin_id", "destination_id", "origin_name", "destination_name"]]
    df5["file"] = 5

    # Fichier 6

    df6 = pd.read_excel(data_path+"/workers_hr/Fichier 6.xlsx")

    df6 = df6.rename(columns={
        "Code postal ville de résidence": "origin_postal_id",
        "Ville de travail": "destination_name"
    })

    df6["origin_postal_id"] = df6["origin_postal_id"].astype(str)
    df6["destination_name"] = df6["destination_name"].str.upper()

    df6 = pd.merge(df6,
                   df_conversion.rename(
                       columns={"commune_id": "origin_id", "postal_id": "origin_postal_id"}),
                   on="origin_postal_id", how="left"
                   )

    df6 = pd.merge(df6,
                   df_names.rename(
                       columns={"office_id": "origin_id", "label": "origin_name"}),
                   on="origin_id", how="left"
                   )

    df6 = pd.merge(df6,
                   df_names.rename(
                       columns={"office_id": "destination_id", "label": "destination_name"}),
                   on="destination_name", how="left"
                   )

    df6 = df6[["origin_id", "destination_id", "origin_name", "destination_name"]]
    df6["file"] = 6

    # Fichier 7

    df7 = pd.read_excel(data_path+"/workers_hr/Fichier 7.xls")

    df7 = df7.rename(columns={
        "Ville1-Résidence": "origin_name",
        "Ville2-Travail": "destination_name"
    })

    df7["origin_name"] = df7["origin_name"].str.upper()
    df7["destination_name"] = df7["destination_name"].str.upper()

    df7 = pd.merge(df7,
                   df_names.rename(
                       columns={"office_id": "origin_id", "label": "origin_name"}),
                   on="origin_name", how="left"
                   )

    df7 = pd.merge(df7,
                   df_names.rename(
                       columns={"office_id": "destination_id", "label": "destination_name"}),
                   on="destination_name", how="left"
                   )

    df7 = df7[["origin_id", "destination_id", "origin_name", "destination_name"]]
    df7["file"] = 7

    # Fichier 8

    df8 = pd.read_excel(data_path+"/workers_hr/Fichier 8.xls", skiprows=[1])

    df8 = df8.rename(columns={
        "Ville1-Résidence": "origin_name",
        "Ville2-Travail": "destination_name"
    })

    df8["origin_name"] = df8["origin_name"].str.upper()
    df8["destination_name"] = df8["destination_name"].str.upper()

    df8 = pd.merge(df8,
                   df_names.rename(
                       columns={"office_id": "origin_id", "label": "origin_name"}),
                   on="origin_name", how="left"
                   )

    df8 = pd.merge(df8,
                   df_names.rename(
                       columns={"office_id": "destination_id", "label": "destination_name"}),
                   on="destination_name", how="left"
                   )

    df8 = df8[["origin_id", "destination_id", "origin_name", "destination_name"]]
    df8["file"] = 8

    # Fichier 9

    # No destination !

    # Fichier 10

    df10 = pd.read_excel(data_path+"/workers_hr/Fichier 10.xlsx")

    df10 = df10.rename(columns={
        "CODE_INSEE": "origin_id",
        "Ville2-Travail": "destination_name"
    })

    df10["origin_id"] = df10["origin_id"].astype(str)
    df10["destination_name"] = df10["destination_name"].str.upper()

    df10 = pd.merge(df10,
                    df_names.rename(
                        columns={"office_id": "origin_id", "label": "origin_name"}),
                    on="origin_id", how="left"
                    )

    df10 = pd.merge(df10,
                    df_names.rename(
                        columns={"office_id": "destination_id", "label": "destination_name"}),
                    on="destination_name", how="left"
                    )

    df10 = df10[["origin_id", "destination_id", "origin_name", "destination_name"]]
    df10["file"] = 10

    # Fichier 11

    df11 = pd.read_excel(data_path+"/workers_hr/Fichier 11.xls", skiprows=[1])

    df11 = df11.rename(columns={
        "Ville1-Résidence": "origin_name",
        "Ville2-Travail": "destination_name"
    })

    df11["origin_name"] = df11["origin_name"].str.upper()
    df11["destination_name"] = df11["destination_name"].str.upper()

    df11 = pd.merge(df11,
                    df_names.rename(
                        columns={"office_id": "origin_id", "label": "origin_name"}),
                    on="origin_name", how="left"
                    )

    df11 = pd.merge(df11,
                    df_names.rename(
                        columns={"office_id": "destination_id", "label": "destination_name"}),
                    on="destination_name", how="left"
                    )

    df11 = df11[["origin_id", "destination_id", "origin_name", "destination_name"]]
    df11["file"] = 11

    # Fichier 12

    df12 = pd.read_excel(data_path+"/workers_hr/Fichier 12.xls", skiprows=[1])

    df12 = df12.rename(columns={
        "Ville1-Résidence": "origin_name",
        "Ville2-Travail": "destination_name"
    })

    df12["origin_name"] = df12["origin_name"].str.upper().str[:-6]
    df12["destination_name"] = df12["destination_name"].str.upper()

    df12 = pd.merge(df12,
                    df_names.rename(
                        columns={"office_id": "origin_id", "label": "origin_name"}),
                    on="origin_name", how="left"
                    )

    df12 = pd.merge(df12,
                    df_names.rename(
                        columns={"office_id": "destination_id", "label": "destination_name"}),
                    on="destination_name", how="left"
                    )

    df12 = df12[["origin_id", "destination_id", "origin_name", "destination_name"]]
    df12["file"] = 12

    # Fichier 13

    df13 = pd.read_excel(data_path+"/workers_hr/Fichier 13.xlsx",
                         skiprows=[1], sheet_name="Feuil1")

    df13 = df13.rename(columns={
        "Code postal": "origin_postal_id",
    })

    df13["origin_postal_id"] = df13["origin_postal_id"].astype(str)

    df13 = pd.merge(df13,
                    df_conversion.rename(
                        columns={"commune_id": "origin_id", "postal_id": "origin_postal_id"}),
                    on="origin_postal_id", how="left"
                    )

    df13 = pd.merge(df13,
                    df_names.rename(
                        columns={"office_id": "origin_id", "label": "origin_name"}),
                    on="origin_id", how="left"
                    )


    df13["destination_id"] = 31555
    df13["destination_name"] = "TOULOUSE"  # We don't know destination!


    ratio_labege = 0.164
    ratio_blagnac = 0.254
    #ratio_colomiers = 0.582

    df_labege = df13.sample(frac=ratio_labege)
    df13 = df13.drop(df_labege.index)
    df_labege["destination_id"] = 31254
    df_labege["destination_name"] = "LABEGE"  # We don't know destination!

    df_blagnac = df13.sample(frac=ratio_blagnac/(1-ratio_labege))
    df13 = df13.drop(df_blagnac.index)
    df_blagnac["destination_id"] = 31069
    df_blagnac["destination_name"] = "BLAGNAC"  # We don't know destination!

    df_colomiers = df13
    df_colomiers["destination_id"] = 31149
    df_colomiers["destination_name"] = "COLOMIERS"  # We don't know destination!

    df13 = pd.concat([df_labege, df_blagnac, df_colomiers])

    df13.loc[df13["Ville"] == "LABEGE", "origin_id"] = 31254
    df13.loc[df13["Ville"] == "LABEGE", "origin_name"] = "LABEGE"
    df13.loc[df13["Ville"] == "LABEGE", "destination_id"] = 31254
    df13.loc[df13["Ville"] == "LABEGE", "destination_name"] = "LABEGE"

    df13.loc[df13["Ville"] == "BLAGNAC", "origin_id"] = 31069
    df13.loc[df13["Ville"] == "BLAGNAC", "origin_name"] = "BLAGNAC"
    df13.loc[df13["Ville"] == "BLAGNAC", "destination_id"] = 31069
    df13.loc[df13["Ville"] == "BLAGNAC", "destination_name"] = "BLAGNAC"

    df13.loc[df13["Ville"] == "COLOMIERS", "origin_id"] = 31149
    df13.loc[df13["Ville"] == "COLOMIERS", "origin_name"] = "COLOMIERS"
    df13.loc[df13["Ville"] == "COLOMIERS", "destination_id"] = 31149
    df13.loc[df13["Ville"] == "COLOMIERS", "destination_name"] = "COLOMIERS"

    df13 = df13[["origin_id", "destination_id", "origin_name", "destination_name"]]
    df13["file"] = 13

    ## Put together
    df = pd.concat([
        df1, df2, df3, df4, df5, df6, df7, df8, df10, df11, df12, df13
    ])
    df = df.dropna()
    df["origin_id"] = df["origin_id"].astype(str)
    df["destination_id"] = df["destination_id"].astype(str)
    df_summary = []

    for file in np.arange(1, 14):
        df_file = df[df["file"] == file]

        initial_count = len(df_file)
        df_file = df_file.dropna()
        final_count = len(df_file)

        df_summary.append({
            "file": file,
            "observations": initial_count,
            "after_cleaning": final_count,
            "valid_data": 100 * final_count / max(initial_count, 1)
        })

    df_summary = pd.DataFrame.from_records(df_summary)

    df_summary.to_csv(data_path+"/processed/al_summary.csv", sep=";", index=False)
    return df


def process_metropole(data_path):
    df_conversion = pd.read_csv(data_path+"/code-postal-code-insee-2015.csv", sep=";")
    df_conversion = df_conversion[["INSEE_COM", "Code_postal"]]
    df_conversion = df_conversion.rename(columns={
        "INSEE_COM": "commune_id", "Code_postal": "postal_id"
    })[["commune_id", "postal_id"]]
    df_conversion["commune_id"] = pd.to_numeric(df_conversion["commune_id"],
                            errors="coerce", downcast="integer")
    df_conversion = df_conversion.dropna()
    df_conversion["commune_id"] = df_conversion["commune_id"].astype(int)
    df_conversion["commune_id"] = df_conversion["commune_id"].astype(str)
    df_conversion["postal_id"] = df_conversion["postal_id"].astype(int)
    df_conversion["postal_id"] = df_conversion["postal_id"].astype(str)

    path = data_path+"/workers_metropole/metropole.xls"
    df = pd.read_excel(path)
    print("Initial", len(df))

    df = df[["Code postal"]]
    df["person_id"] = np.arange(len(df))

    df = df.rename(columns={
        "Code postal": "postal_id"
    })
    df["postal_id"] = df["postal_id"].astype(str)

    df = pd.merge(df, df_conversion, on="postal_id")
    df = df.drop_duplicates("person_id")

    df["origin_id"] = df["commune_id"]
    df["destination_id"] = "31555"

    df = df.dropna()
    print("Final", len(df))

    df = df[["person_id", "origin_id", "destination_id"]]
    return df


def process_region(data_path):
    path = data_path+"/workers_region/region.xlsx"
    df = pd.read_excel(path)

    before_count = len(df)
    df = df[df["Ville2-Travail"] == "Toulouse"]
    after_count = len(df)

    print("Filtered %d/%d (%.2f%%) persons not working in Toulouse" % (
        (before_count - after_count), before_count, 100.0
        * (before_count - after_count) / before_count
    ))

    df["origin_id"] = df["CODE_INSEE"].astype(str)
    df["origin_id"] = pd.to_numeric(df["origin_id"],
                            errors="coerce", downcast="integer")
    df["destination_id"] = "31555"
    df["person_id"] = np.arange(len(df))
    df = df[["person_id", "origin_id", "destination_id"]]
    df = df.dropna()
    df["origin_id"] = df["origin_id"].astype(int)
    df["origin_id"] = df["origin_id"].astype(str)
    df.reset_index(drop=True)
    return df


def get_population(data_path, departments):
    """
    Call the preprocessing procedures to compute the population
    """
    path = f"{data_path}/processed/persons.csv"
    if not os.path.isfile(path):
        print("Computing population...")
        communes_df = com.get_communes(data_path)

        al_df = process_action_logement(data_path, communes_df)
        #al_df.to_csv(data_path+"/processed/od_al.csv", sep=";", index=False)
        al_df = al_df[["origin_id", "destination_id"]]

        met_df = process_metropole(data_path)
        #met_df.to_csv(data_path+"/processed/od_metropole.csv", sep=";", index=False)
        met_df = met_df[["origin_id", "destination_id"]]

        reg_df = process_region(data_path)
        #reg_df.to_csv(data_path+"/processed/od_region.csv", index=False)
        reg_df = reg_df[["origin_id", "destination_id"]]

        persons_df = pd.concat([al_df, met_df, reg_df])

        persons_df = persons_df[persons_df["origin_id"].str[0:2].isin(departments)]
        persons_df = persons_df[persons_df["destination_id"].str[0:2].isin(departments)]

        persons_df["person_id"] = np.arange(len(persons_df))
        persons_df.dropna(inplace=True)
        persons_df.to_csv(path, index=False)

    return pd.read_csv(path, dtype=str)
