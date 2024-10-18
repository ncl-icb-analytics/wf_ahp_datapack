'''
Pipeline for outputs sourced from the NHS Workforce Statistics source data
Source: https://digital.nhs.uk/data-and-information/publications/statistical/nhs-workforce-statistics/
'''
import os
import pandas as pd
from datetime import datetime as dt

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
    sr_shorthand_map = {}

    for role in df_flu.iterrows():
        fuzzy_name = role[1].iloc[0]
        front_name = role[1].iloc[1]
        front_short = role[1].iloc[2]

        sr_values = fuzzy_search(df_nwfs, "staff_role", fuzzy_name)
        for sr in sr_values:
            sr_map[sr] = front_name

        sr_shorthand_map[front_name] = front_short

    #Apply the frontend mapping
    df_nwfs["staff_role"] = df_nwfs["staff_role"].map(sr_map)

    #Add the Role Shorthand column
    df_nwfs["staff_role_shorthand"] = df_nwfs["staff_role"].map(
        sr_shorthand_map)
    
    return df_nwfs

#Remove the "Band" from the afc_band column and shorten the Non-AfC value
def format_afc_col(val):
    if val[0] == "N":
        return "Non-AfC"
    else:
        return val.split(" ")[1]

#Zero fill for column values that do not appear in the data
def zero_fill(df, column_name, column_values):

    #Create copy of the input data frame
    df_zfed = df.copy()
    num_of_cols = df_zfed.shape[1]
    dummy_row = []
    for i in range(num_of_cols):
        dummy_row.append(None)

    #Get list of values that do appear in the data
    values_in_data = df[column_name].unique()

    #Add dummy rows for the missing data
    for value in column_values:
        if value not in values_in_data:
            df_zfed.loc[df_zfed.shape[0]] = dummy_row
            df_zfed.loc[df_zfed.shape[0]-1][column_name] = 0

    return df_zfed

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

    #Add the Org Shorthand column
    df_src["org_shorthand"] = df_src["org_code"].map(
        dict(
            map(
                lambda i,j : (i,j) , 
                settings["org_codes"], 
                settings["org_shorts"]
            )
        )
    )

    #Add formatted period column
    df_src["period_datapoint"] = pd.to_datetime(
        df_src["period"]).dt.strftime('%b-%y')

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
            order=afc_bands,
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

    plt.suptitle("NCL AHP Role WTE by AfC Band", fontsize=20, fontweight="bold")
    plt.tight_layout(rect=[0, 0, 1, 0.98])
    plt.savefig('./output/current/wte_by_afcband.png', 
                dpi=300, bbox_inches='tight')

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
    org_shorts = settings["org_shorts"]
    org_shorts.sort()

    # Loop over each axis and plot the barplots
    for i, ax in enumerate(axes):
        df_role = df.copy()[df["staff_role"] == ahp_roles[i]]

        #Aggregate data
        df_role = df_role.groupby('org_shorthand', as_index=False)['wte'].sum()

        sns.barplot(
            x="org_shorthand", 
            y="wte", 
            data=df_role,
            order=org_shorts,
            ax=ax,
            color="#242853",
        )

        #Format the x axis to be consistent for all graphs
        ax.set_xticks(range(len(org_shorts)))
        ax.set_xticklabels(org_shorts, fontsize=8)

        #Remove box from graphs
        sns.despine()

        # Format the titles and axes
        ax.set_title(ahp_roles[i])
        ax.set_xlabel(None)
        ax.set_ylabel('WTE')
        ax.yaxis.set_major_locator(MaxNLocator(integer=True))

    # Show the plot
    #plt.show()

    plt.suptitle("NCL AHP Role WTE by Provider", fontsize=20, fontweight="bold")
    plt.tight_layout(rect=[0, 0, 1, 0.98])
    plt.savefig('./output/current/wte_by_org.png', 
                dpi=300, bbox_inches='tight')

#Plot AHP Role against Organisation
def plot_org_by_role (df, settings):

    #Only consider latest data
    df = df[df["period"] == df["period"].max()]

    #Load list of AHP roles (shorthand)
    df_flu = pd.read_csv("docs/nwfs_lookup.csv")
    ahp_roles = df_flu["role_shorthand"].unique()
    ahp_roles.sort()

    # Initialize the figure and axes for a 4x3 grid
    fig, axes = plt.subplots(3, 4, figsize=(18, 9))
    axes = axes.flatten()

    #Load list of orgs
    org_shorts = settings["org_shorts"]

    # Loop over each axis and plot the barplots
    for i, ax in enumerate(axes):

        if i < 10:
            df_org = df.copy()[df["org_shorthand"] == org_shorts[i]]

            #Aggregate data
            df_org = df_org.groupby(
                'staff_role_shorthand', as_index=False)['wte'].sum()

            sns.barplot(
                x="staff_role_shorthand", 
                y="wte", 
                data=df_org,
                order=ahp_roles,
                ax=ax,
                color="#242853",
            )

            #Format the x axis to be consistent for all graphs
            ax.set_xticks(range(len(ahp_roles)))
            ax.set_xticklabels(ahp_roles, fontsize=8)

            #Remove box from graphs
            sns.despine()

            # Format the titles and axes
            ax.set_title(org_shorts[i])
            ax.set_xlabel(None)
            ax.set_ylabel('WTE')
            ax.yaxis.set_major_locator(MaxNLocator(integer=True))

    # Add NCL overall as a plot (fig 10)
    #Aggregate data
    df_ncl = df.copy().groupby(
        'staff_role_shorthand', as_index=False)['wte'].sum()

    sns.barplot(
        x="staff_role_shorthand", 
        y="wte", 
        data=df_ncl,
        order=ahp_roles,
        ax=axes[10],
        color="#242853",
    )

    #Format the x axis to be consistent for all graphs
    axes[10].set_xticks(range(len(ahp_roles)))
    axes[10].set_xticklabels(ahp_roles, fontsize=8)

    #Remove box from graphs
    sns.despine()

    # Format the titles and axes
    axes[10].set_title("NCL")
    axes[10].set_xlabel(None)
    axes[10].set_ylabel('WTE')
    axes[10].yaxis.set_major_locator(MaxNLocator(integer=True))

    #Include key for Staff Roles
    # table_data = df_flu[["role_shorthand", "staff_role_frontend"]].values
    # sr_table = axes[11].table(
    #     cellText=table_data, colLabels=None, 
    #     loc='center', cellLoc='center',
    #     bbox = [0, 0, 1, 1], fontsize=20)
    # axes[11].axis("off")

    table_data = df_flu[["role_shorthand", "staff_role_frontend"]].values
    table_data = sorted(table_data, key=lambda x: x[0])
    table_text = ""
    for row in table_data:
        spaces = 4 - len(row[0])
        table_text += row[0] + " "*spaces + ": " + row[1] + "\n"
    table_text = table_text[:-1]

    axes[11].text(0, 0.5, table_text, family='Inconsolata', fontsize=12,
                  horizontalalignment='left', verticalalignment='center')
    axes[11].axis("off")

    # Show the plot
    #plt.show()

    plt.suptitle("NCL Provider AHP WTE by Staff Role", 
                 fontsize=20, fontweight="bold")
    plt.tight_layout(rect=[0, 0, 1, 0.98])
    plt.savefig('./output/current/wte_by_role.png', 
                dpi=300, bbox_inches='tight')#, transparent=True)

#Plot year on year growth
def plot_yoy_by_org (df, settings):

    #Load list of orgs
    org_shorts = settings["org_shorts"]
    org_shorts.sort()

    #Aggregate data
    df_trend = df.groupby(['period_datapoint', 'org_shorthand'], as_index=False)['wte'].sum()

    fig, ax = plt.subplots(figsize=(6, 4))

    ncl_palette = sns.color_palette(
        ["#8136CD", "#D12D8A", "#6CB52D", "#408DB4", "#6796f7",
         "#7C2855", "#8A1538", "#006747", "#33599f", "#330072"])

    sns.barplot(
        x="org_shorthand", 
        y="wte",
        hue="period_datapoint",
        data=df_trend,
        order=org_shorts,
        ax=ax,
        palette=ncl_palette
    )

    #Format the x axis to be consistent for all graphs
    ax.set_xticks(range(len(org_shorts)))
    ax.set_xticklabels(org_shorts, fontsize=8)

    #Remove box from graphs
    sns.despine()

    # Format the titles and axes
    #ax.set_title(ahp_roles[i])
    ax.set_xlabel(None)
    ax.set_ylabel('WTE')
    ax.yaxis.set_major_locator(MaxNLocator(integer=True))
    ax.legend(title="Period")

    plt.suptitle("NCL AHPs by Provider Trend", fontsize=16, fontweight="bold")
    plt.tight_layout(rect=[0, 0, 1, 0.98])
    plt.savefig('./output/trends/by_org.png', 
                dpi=300, bbox_inches='tight')

#Plot year on year growth
def plot_yoy_by_role (df, settings):

    #Sort the data by the x axis column
    df.sort_values(by='staff_role_shorthand', inplace=True)

    #Load list of AHP roles (shorthand)
    df_flu = pd.read_csv("docs/nwfs_lookup.csv")
    ahp_roles = df_flu["role_shorthand"].unique()
    ahp_roles.sort()

    #Aggregate data
    df_trend = df.groupby(
        ['period_datapoint', 'staff_role_shorthand'], as_index=False
        )['wte'].sum()
    
    periods = len(df_trend["period_datapoint"].unique())

    fig, axes = plt.subplots(
        1, 2, figsize=(9, 4), gridspec_kw={"width_ratios": [2, 1]})

    ncl_palette = sns.color_palette(
        ["#8136CD", "#D12D8A", "#6CB52D", "#408DB4", "#6796f7",
         "#7C2855", "#8A1538", "#006747", "#33599f", "#330072"][:periods])

    sns.barplot(
        x="staff_role_shorthand", 
        y="wte",
        hue="period_datapoint",
        data=zero_fill(df_trend, "staff_role_shorthand", ahp_roles),
        order=ahp_roles,
        ax=axes[0],
        palette=ncl_palette
    )

    #Format the x axis to be consistent for all graphs
    axes[0].set_xticks(range(len(ahp_roles)))
    axes[0].set_xticklabels(ahp_roles, fontsize=8)

    #Remove box from graphs
    sns.despine()

    # Format the titles and axes
    #ax.set_title(ahp_roles[i])
    axes[0].set_xlabel(None)
    axes[0].set_ylabel('WTE')
    axes[0].yaxis.set_major_locator(MaxNLocator(integer=True))
    axes[0].legend(title="Period")

    #Add Role mapping as a seperate ax
    table_data = df_flu[["role_shorthand", "staff_role_frontend"]].values
    table_data = sorted(table_data, key=lambda x: x[0])
    table_text = ""
    for row in table_data:
        spaces = 4 - len(row[0])
        table_text += row[0] + " "*spaces + ": " + row[1] + "\n"
    table_text = table_text[:-1]

    axes[1].text(0, 0.5, table_text, family='Inconsolata', fontsize=12,
                  horizontalalignment='left', verticalalignment='center')
    axes[1].axis("off")

    plt.suptitle("NCL AHPs by AHP Role", fontsize=16, fontweight="bold")
    plt.tight_layout(rect=[0, 0, 1, 0.98])
    plt.savefig('./output/trends/by_role.png', 
                dpi=300, bbox_inches='tight')

#Main function for the pipeline
def nhs_wf_stats(settings):

    #Load the data
    df_nwfs = load_nwfs_data(settings=settings)

    df_nwfs.to_csv("ncldata.csv", index=False)

    #Plot AHP Staff Role by Band
    plot_role_by_band(df_nwfs, settings=settings)

    #Plot AHP Staff Role by Organisation
    plot_role_by_org(df_nwfs, settings)

    #Plot Org AHP WTE by Staff Role
    plot_org_by_role(df_nwfs, settings)

    #Plot annual data
    plot_yoy_by_org(df_nwfs, settings)
    plot_yoy_by_role(df_nwfs, settings)