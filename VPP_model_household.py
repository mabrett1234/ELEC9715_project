#VPP_model_household
#To use: import VPP_model_household as household
"""
# This code reads in a household's PV and load data and gives the BESS data and writes back to the Excel file
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

# Clean out invalid data due to metering issues, e.g. negative demand or PV generation
df_house_data = df_house_data.fillna(0)

# Ensure no negative values (metering errors)
df_house_data['GC'] = df_house_data['GC'].clip(lower=0)
df_house_data['PV'] = df_house_data['PV'].clip(lower=0)

# If CL exists, clean it as well
if 'CL' in df_house_data.columns:
    df_house_data['CL'] = df_house_data['CL'].clip(lower=0)


# Code to generate data for BESS given PV and load demand
# BESS model parameters (user-defined)
bess_capacity = float(input("Enter BESS capacity (kWh): "))   # kWh
bess_min_soc = float(input("Enter minimum SoC (kWh): "))    # kWh (reserve level)
bess_init_soc = float(input("Enter initial SoC (kWh): "))  # kWh (initial state of charge)

# Validate inputs
if bess_capacity <= 0:
    raise ValueError("BESS capacity must be > 0")

if bess_min_soc < 0 or bess_min_soc > bess_capacity:
    raise ValueError("Minimum SoC must be between 0 and capacity")

if bess_init_soc < bess_min_soc or bess_init_soc > bess_capacity:
    raise ValueError("Initial SoC must be between min SoC and capacity")

# Combine GC and CL for total demand
# NOTE: If CL column does not exist, default to GC only
if 'CL' in df_house_data.columns:
    dataLoad = df_house_data['GC'] + df_house_data['CL']
else:
    dataLoad = df_house_data['GC']

# Extract PV data
dataPV = df_house_data['PV']

# Initialise arrays to store BESS behaviour
soc = np.zeros(len(dataLoad))            # State of Charge (kWh)
charge = np.zeros(len(dataLoad))         # Charging energy (kWh)
discharge = np.zeros(len(dataLoad))      # Discharging energy (kWh)

# Set initial SoC
soc[0] = bess_init_soc

# BESS operation loop
for t in range(1, len(dataLoad)):

    # Net energy balance (kWh over 30 min)
    net_energy = dataPV.iloc[t] - dataLoad.iloc[t]

    # Case 1: Excess PV -> charge BESS
    if net_energy > 0:
        available_capacity = bess_capacity - soc[t-1]
        charge[t] = min(net_energy, available_capacity)
        discharge[t] = 0.0

    # Case 2: Deficit -> discharge BESS
    elif net_energy < 0:
        available_energy = soc[t-1] - bess_min_soc
        discharge[t] = min(-net_energy, max(available_energy, 0))
        charge[t] = 0.0

    # Case 3: Balanced
    else:
        charge[t] = 0.0
        discharge[t] = 0.0

    # Update SoC
    soc[t] = soc[t-1] + charge[t] - discharge[t]

    # Enforce bounds (safety check)
    if soc[t] > bess_capacity:
        soc[t] = bess_capacity
    if soc[t] < bess_min_soc:
        soc[t] = bess_min_soc

# Append BESS data to dataframe
df_house_data['BESS SoC (kWh)'] = soc   # State of Charge of BESS
df_house_data['BESS Charge (kWh)'] = charge     # Amount of kWh that BESS charges
df_house_data['BESS Discharge (kWh)'] = discharge   # Amount of kWh BESS discharges

# Write back to Excel (overwrite file with new columns appended)
with pd.ExcelWriter("vic_house_data_with_bess.xlsx", engine='openpyxl', mode='a', if_sheet_exists='overlay') as writer:
    df_house_data.to_excel(writer, index=False)