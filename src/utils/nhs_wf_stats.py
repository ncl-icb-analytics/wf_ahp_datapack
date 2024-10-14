'''
Pipeline for outputs sourced from the NHS Workforce Statistics source data
Source: https://digital.nhs.uk/data-and-information/publications/statistical/nhs-workforce-statistics/
'''
import os
import pandas as pd

#Find all unique column values for a specified column that contains the target
#I am fully aware this is not what fuzzy matching is
def fuzzy_search(df_nwfs, col_name, target_string):
    
    #Remove all rows without the target_string
    s_res = df_nwfs[df_nwfs[col_name].str.contains(target_string)][col_name]

    return s_res.unique().tolist()

#Function to map src data staff roles to consistent front end names
def nwfs_staff_role_fuzzy_mapping(df_nwfs, settings):

    #Load the AHP staff role map
    df_flu = pd.read_csv("docs/nwfs_lookup.csv")

    #Build the map of existing row names to front end names
    sr_map = {}

    for role in df_flu.iterrows():
        fuzzy_name = role[1].iloc[0]
        front_name = role[1].iloc[1]

        sr_values = fuzzy_search(df_nwfs, "staff_role", fuzzy_name)
        for sr in sr_values:
            sr_map[sr] = front_name

    #Apply the mapping
    df_nwfs["mapped"] = df_nwfs["staff_role"].map(sr_map)
    
    return df_nwfs

#Load the source data from the nwfs source files
def load_nwfs_data(settings):

    #Load source data###########################################################
    data_files = os.listdir(settings["nwfs_path"])
    
    df_src = pd.concat(
        [pd.read_csv(
            os.path.join(settings["nwfs_path"], data_file)
            ) for data_file in data_files], 
        ignore_index=True)

    #Format#####################################################################

    #Relevant Columns
    df_src = df_src[[
        "Date", 
        "Org code", 
        settings["nwfs_colahp"], 
        settings["nwfs_colrole"], 
        settings["nwfs_colband"], 
        "Total FTE"
    ]]

    #Rename Columns
    df_src.rename(
        columns={
            "Date": "period", 
            "Org code": "org_code", 
            settings["nwfs_colahp"]: "staff_group_2", 
            settings["nwfs_colrole"]: "staff_role", 
            settings["nwfs_colband"]: "afc_band",
            "Total FTE": "wte"
        },
        inplace=True
    )

    #NCL only
    ncl_orgs = settings["org_codes"]
    df_src = df_src[df_src["org_code"].isin(ncl_orgs)]

    #AHP only
    sg2_values = fuzzy_search(df_src, "staff_group_2", "_Allied")
    df_src = df_src[df_src["staff_group_2"].isin(sg2_values)]
    df_src.drop("staff_group_2", axis=1, inplace=True)

    ##Format staff role column using fuzzy function
    df_src = nwfs_staff_role_fuzzy_mapping(df_src, settings=settings)

    print(df_src.head())

#Main function for the pipeline
def nhs_wf_stats(settings):

    #Load the data
    df_nwfs = load_nwfs_data(settings=settings)