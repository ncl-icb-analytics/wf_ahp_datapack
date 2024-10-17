'''
Pipeline for outputs sourced from the NHS Workforce Statistics source data
Source: https://digital.nhs.uk/data-and-information/publications/statistical/nhs-workforce-statistics/
'''
import os
import pandas as pd

import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator
import seaborn as sns

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
    df_nwfs["staff_role"] = df_nwfs["staff_role"].map(sr_map)
    
    return df_nwfs

def format_afc_col(val):
    if val[0] == "N":
        return "Non-AfC"
    else:
        return val.split(" ")[1]

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

    #Format the AfC Band column
    df_src["afc_band"] = df_src["afc_band"].apply(format_afc_col)

    return df_src

#Plot AHP Role against Band
def plot_role_by_band(df, settings):

    #Only consider latest data
    df = df[df["period"] == df["period"].max()]

    #Load list of AHP roles
    ahp_roles = pd.read_csv(
        "docs/nwfs_lookup.csv")["staff_role_frontend"].unique()
    ahp_roles.sort()

    # Initialize the figure and axes for a 4x3 grid
    fig, axes = plt.subplots(3, 4, figsize=(16, 9))
    axes = axes.flatten()

    # Get all bands from the data
    afc_bands = df["afc_band"].unique()
    afc_bands.sort()

    # Loop over each axis and plot the barplots
    for i, ax in enumerate(axes):
        df_role = df.copy()[df["staff_role"] == ahp_roles[i]]

        #Aggregate data
        df_role = df_role.groupby('afc_band', as_index=False)['wte'].sum()

        sns.barplot(
            x="afc_band", 
            y="wte", 
            data=df_role,
            ax=ax,
            color="#242853",
        )

        #Format the x axis to be consistent for all graphs
        ax.set_xticks(range(len(afc_bands)))
        ax.set_xticklabels(afc_bands)

        #Remove box from graphs
        sns.despine()

        # Format the titles and axes
        ax.set_title(ahp_roles[i])
        ax.set_xlabel('AFC Band')
        ax.set_ylabel('WTE')
        ax.yaxis.set_major_locator(MaxNLocator(integer=True))

    # Show the plot
    #plt.show()

    plt.suptitle("AHP Role WTE by AfC Band", fontsize=20)
    plt.tight_layout(rect=[0, 0, 1, 0.98])
    plt.savefig('./output/role_by_band/wte_by_afc_band.png', dpi=300, bbox_inches='tight')

    # Export the NCL data
    #df.to_csv("ncldata.csv", index=False)

#Plot AHP Role against Organisation
def plot_role_by_org (df, settings):

    #Only consider latest data
    df = df[df["period"] == df["period"].max()]

    #Load list of AHP roles
    ahp_roles = pd.read_csv(
        "docs/nwfs_lookup.csv")["staff_role_frontend"].unique()
    ahp_roles.sort()

    # Initialize the figure and axes for a 4x3 grid
    fig, axes = plt.subplots(3, 4, figsize=(16, 9))
    axes = axes.flatten()

    #Load list of orgs
    org_codes = settings["org_codes"]
    org_shorts = settings["org_shorts"]

    # Loop over each axis and plot the barplots
    for i, ax in enumerate(axes):
        df_role = df.copy()[df["staff_role"] == ahp_roles[i]]

        #Aggregate data
        df_role = df_role.groupby('org_code', as_index=False)['wte'].sum()

        sns.barplot(
            x="org_code", 
            y="wte", 
            data=df_role,
            ax=ax,
            color="#242853",
        )

        #Format the x axis to be consistent for all graphs
        ax.set_xticks(range(len(org_codes)))
        ax.set_xticklabels(org_codes)

        #Remove box from graphs
        sns.despine()

        # Format the titles and axes
        ax.set_title(ahp_roles[i])
        ax.set_xlabel('Provider')
        ax.set_ylabel('WTE')
        ax.yaxis.set_major_locator(MaxNLocator(integer=True))

    # Show the plot
    #plt.show()

    plt.suptitle("AHP Role WTE by Provider", fontsize=20)
    plt.tight_layout(rect=[0, 0, 1, 0.98])
    plt.savefig('./output/role_by_org/wte_by_afc_org.png', dpi=300, bbox_inches='tight')

#Main function for the pipeline
def nhs_wf_stats(settings):

    #Load the data
    df_nwfs = load_nwfs_data(settings=settings)

    #df_nwfs.to_csv("sample.csv", index=False)

    #Plot AHP Staff Role by Band
    #plot_role_by_band(df_nwfs, settings=settings)

    #Plot AHP Staff Role by Organisation
    plot_role_by_org (df_nwfs, settings)