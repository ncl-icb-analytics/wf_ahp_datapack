'''
Pipeline for outputs sourced from the PWR Forms (in Sandpit)
'''

import pandas as pd
import ncl_sqlsnippets as snips

import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator
import seaborn as sns

#Find all unique column values for a specified column that contains the target
#I am fully aware this is not what fuzzy matching is
def fuzzy_search(df, col_name, target_string):
    
    #Remove all rows without the target_string
    s_res = df[df[col_name].str.contains(target_string)][col_name]

    return s_res.unique().tolist()

#Function to map src data staff roles to consistent front end names
def nwfs_staff_role_fuzzy_mapping(df, settings):

    #Load the AHP staff role map
    df_flu = pd.read_csv("docs/nwfs_lookup.csv")

    #Build the map of existing row names to front end names
    sr_map = {}
    sr_shorthand_map = {}

    for role in df_flu.iterrows():
        fuzzy_name = role[1].iloc[0]
        front_name = role[1].iloc[1]
        front_short = role[1].iloc[2]

        sr_values = fuzzy_search(df, "staff_role", fuzzy_name)
        for sr in sr_values:
            sr_map[sr] = front_name

        sr_shorthand_map[front_name] = front_short

    #Apply the frontend mapping
    df["staff_role"] = df["staff_role"].map(sr_map)

    #Add the Role Shorthand column
    df["staff_role_shorthand"] = df["staff_role"].map(
        sr_shorthand_map)
    
    return df

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

#Load and execute the PWR SQL Query
def load_pwr_data(settings):
    #Load the query script
    f = open(f"./docs/pwr_extract.sql", 'r')
    sql_query = f.read()
    f.close()

    #Execute the query and load the data
    engine = snips.connect(settings["sql_address"], settings["pwr_database"])
    df_res = snips.execute_sfw(engine, sql_query)

    #Apply fuzzy matching functions
    df_res = nwfs_staff_role_fuzzy_mapping(df_res, settings)

    return df_res

#Plot AHP WTE trend by contract
def plot_wte_by_contract(df, settings):

    # Initialize the figure and axes for a 4x3 grid
    fig, axes = plt.subplots(1, 2, figsize=(12, 6))
    axes = axes.flatten()

    #Aggregate data
    df_agg = df.copy()[["fin_year", "fin_month", "contract", "wte"]].groupby(
        ['fin_year', 'fin_month', "contract"], as_index=False)['wte'].sum()
    
    #Add combined date column
    df_agg["period"] = df_agg["fin_year"] + "_" + df_agg["fin_month"].astype(str)
    
    #Split data into substantive and non-substantive
    df_sub = df_agg[df_agg["contract"] == "Substantive"]
    df_temp = df_agg[df_agg["contract"] != "Substantive"]

    dfs = [df_sub, df_temp]

    #Pre-calculate x axis formatting variables
    xticks_months = df_sub["fin_month"].to_list()
    #Convert months into names
    month_map = {1:"Apr", 2:"May", 3:"Jun", 4:"Jul",
                 5:"Aug", 6:"Sep", 7:"Oct", 8:"Nov",
                 9:"Dec", 10:"Jan", 11:"Feb", 12:"Mar"}
    xticks_months = [month_map[item] for item in xticks_months]

    xticks_years = df_sub["fin_year"].unique()
    #xticks_years = ["\n\n\n" + s for s in xticks_years]

    # Loop over each axis and plot the barplots
    for i, ax in enumerate(axes):
        #Get data for this axes
        df_ax = dfs[i].copy()

        if i == 0:
            ax_name = "Substantive"
            inc_legend = False
        else:
            ax_name = "Band & Agency"
            inc_legend = True

        sns.lineplot(
            data=df_ax,
            x="period",
            y="wte",
            hue="contract",
            legend=inc_legend,
            ax=ax
        )

        if inc_legend:
            ax.legend(title="Contract")

        #Remove box from graphs
        sns.despine()

        #Format the primary x axis (months)
        ax.set_xticks(range(len(xticks_months)))
        ax.set_xticklabels(xticks_months, rotation=90)
        ax.tick_params("x", width=1)
        ax.set_xlabel(None)

        #Add the Year Labels
        sec = ax.secondary_xaxis(location=0)
        sec.set_xticks([5.5,17.5,26.5], labels=xticks_years)
        sec.tick_params("x", length=0, pad=35)
        
        #Add Seperators for the years
        sec2 = ax.secondary_xaxis(location=0)
        sec2.set_xticks([-0.5, 11.5, 23.5, 29.5], labels=[])
        sec2.tick_params("x", length=40, width=1)
        ax.set_xlim(-0.6, 29.6)

        # Format the titles and axes
        ax.set_title(f"NCL Secondary Care AHP - SIP Trend ({ax_name})", 
                     fontweight="bold")
        ax.set_ylabel('WTE')
        ax.yaxis.set_major_locator(MaxNLocator(integer=True))
        ax.grid(True, axis="y", color="lightgray", alpha=0.5)

    # Show the plot
    #plt.show()

    #plt.suptitle("NCL Secondary Care AHP - SIP Trend", fontsize=20, fontweight="bold")
    plt.tight_layout(rect=[0, 0, 1, 0.98])
    plt.savefig('./output/pwr/wte_trend.png', 
                dpi=300, bbox_inches='tight')

#Plot function for vacancy by AHP staff role
def plot_yoy_by_role_raw(df, settings):
    #Sort the data by the x axis column
    df.sort_values(by='staff_role_shorthand', inplace=True)

    #Load list of AHP roles (shorthand)
    df_flu = pd.read_csv("docs/nwfs_lookup.csv")
    ahp_roles = df_flu["role_shorthand"].unique()
    ahp_roles.sort()

    #Filter to only data with the most recent month
    month_latest = df[df["fin_year"] == df["fin_year"].max()]["fin_month"].max()
    df_month = df[df["fin_month"] == month_latest]

    #Aggregate data
    df_trend = df_month.groupby(
        ['period_datapoint', 'staff_role_shorthand'], as_index=False
        )['vacancy'].sum()
    
    periods = len(df_trend["period_datapoint"].unique())

    fig, axes = plt.subplots(
        1, 2, figsize=(9, 4), gridspec_kw={"width_ratios": [2, 1]})

    ncl_palette = sns.color_palette(
        ["#8136CD", "#D12D8A", "#6CB52D", "#408DB4", "#6796f7",
         "#7C2855", "#8A1538", "#006747", "#33599f", "#330072"][:periods])

    sns.barplot(
        x="staff_role_shorthand", 
        y="vacancy",
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
    axes[0].set_ylabel('Vacancy (WTE)')
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

    plt.suptitle("NCL AHPs Vacancy (WTE) by AHP Role", fontsize=16, fontweight="bold")
    plt.tight_layout(rect=[0, 0, 1, 0.98])
    plt.savefig('./output/pwr/vac_raw_by_role.png', 
                dpi=300, bbox_inches='tight')

#Main function for the pipeline
def pwr_trends(settings):

    print("Executing PWR Trends Pipeline\n")

    #Load the data from the Sandpit
    df_pwr = load_pwr_data(settings=settings)

    #Line chart showing trend by contract
    plot_wte_by_contract(df_pwr, settings)

    #print(df_pwr.head())

    #Bar plot showing year on year growth for each role
    plot_yoy_by_role_raw(df_pwr, settings)
