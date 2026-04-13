#VPP_model_household
#To use: import VPP_model_household as household
"""
TODO: Code overview
"""

# Imports
import os
import numpy as np
import pandas as pd
from matplotlib import pyplot as plt

# Classes
class Household:
    """
    Organise data of one household to be easily accessible
    Try keep this structured so the VPP rules can be applied easily
    """

    def __init__(
                self,
                pv_cap,
                df_demand,
                df_pv,
                label=None
    ):
        self.pvCap = pv_cap
        self.dataDemand = df_demand
        self.dataPV = df_pv
        if label != None:
            self.label = label
        else:
            self.label = "no_name"

    def __str__(self):
        return "Type: Household, name: {}".format(self.label)

    # Other functions
#TODO: Import household data: Store as two dataframes

# Grab entire excel file and convert to pandas dataframe
def check_fname_in_dir(file_name, ext):
    valid_fnames = os.listdir()
    file_name = file_name.split('/')[-1]
    if valid_fnames.count(file_name) <= -1:
        print("ERR:File name chosen not in current directory.")
        print("Please try again with", end = "")
        print(" a {} file in the current directory:".format(ext))
        for fname in valid_fnames:
            if fname.endswith(ext):
                print("\t{}".format(fname))

def import_household_data(file_name, dbug_lvl):
    # Check the file name is in current directory and excel
    check_fname_in_dir(file_name, ".xlsx")
    # Import the data with pandas.
    df = pd.read_excel(
                        file_name
    )
    # Print out imported info, with dbug_lvl controlling verbosity
    if (dbug_lvl == 2):
        print(df)
    elif (dbug_lvl == 1):
        print(df.head())
    # Return the data as a pandas dataframe
    return df

# Initial test: Just using only one household
df_house_data = import_household_data("vic_house_data.xlsx", 2)

# Split into pandas dataframe for demand and pv
household = Household(
                        6.0, #PV Capacity
                        df_house_data['GC'], # Demand
                        df_house_data['PV'],  # PV generation
                        label = 69 # Household number (end of my zid)
)

# Clean the data: detect any weird metering issues or households

