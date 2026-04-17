#VPP_model_household
#To use: import VPP_model_household as household
"""
Read in a household PV and load data
Calculate BESS data
Write result into an Excel file
"""

# Imports
import os
import numpy as np
import pandas as pd
from matplotlib import pyplot as plt

# Consants*
PV_CAP_DEFAULT = 6.0
BESS_CAP_DEFAULT = 20.0
BESS_SOC_MIN_DEFAULT = 20.0*0.2
BESS_SOC_INIT_DEFAULT = BESS_CAP_DEFAULT

# Classes
class Household:
    """
    Organise data of one household to be easily accessible
    Try keep this structured so the VPP rules can be applied easily
    """

    def __init__(
                self,
                pv_arr,
                gc_arr,
                cl_arr,
                pv_cap=PV_CAP_DEFAULT,
                bess_capacity=BESS_CAP_DEFAULT,
                bess_soc_min=BESS_SOC_MIN_DEFAULT,
                bess_soc_init=BESS_SOC_INIT_DEFAULT,
                label=None
    ):
        self.pvCapacity = pv_cap
        # Just going to use defaults for these for most analysis
        self.bessCapacity = bess_capacity
        self.bessSocMin=bess_soc_min
        self.bessSocInit=bess_soc_init
        # Annual timeseries
        self.data = pd.DataFrame(
                                    {
                                        "GC":gc_arr,
                                        "PV":pv_arr,
                                        "CL":cl_arr
                                    }
        )
        if label != None:
            self.label = label
        else:
            self.label = "no_name"

    def __str__(self):
        return "Type: Household, name: {}".format(self.label)
    
    def clean_data(self):
        for i in range(0, len(self.data.columns)):
            self.data.iloc[:, i] = self.data.iloc[:, i].clip(lower=0)

    def combine_demand(self):
        # Assuming CL column exists.
        self.data['load'] = self.data['GC'] + self.data['CL']

    def calc_bess_data(self):
        n = len(self.data.index)
        soc = np.zeros(n)            # State of Charge (kWh)
        charge = np.zeros(n)         # Charging energy (kWh)
        discharge = np.zeros(n)      # Discharging energy (kWh)

        # Set initial SoC
        soc[0] = self.bessSocInit

        # BESS operation loop
        for t in range(1, n):
            # Net energy balance (kWh over 30 min)
            net_energy = self.data['PV'].iloc[t] - self.data['load'].iloc[t]

            # Case 1: Excess PV -> charge BESS
            available_capacity = self.bessCapacity - soc[t-1]
            available_energy = soc[t-1] - self.bessSocMin
            # all elements set to zero already

            # Case 1: Excess PV -> charge BESS
            if net_energy > 0:
                charge[t] = min(net_energy, available_capacity)
            # Case 2: Not enough PV -> discharge BESS
            elif net_energy < 0:
                discharge[t] = min(
                                    -net_energy,
                                max(available_energy, 0)
                )
            # Update SoC
            soc[t] = soc[t-1] + charge[t] - discharge[t]
            # Enforce bounds (safety check)
            if soc[t] > self.bessCapacity:
                soc[t] = self.bessCapacity
            if soc[t] < self.bessSocMin:
                soc[t] = self.bessSocMin

        # Append BESS data to dataframe
        self.data['BESS SoC (kWh)'] = soc   # State of Charge
        self.data['BESS Charge (kWh)'] = charge # kWh charges
        self.data['BESS Discharge (kWh)'] = discharge # kWh discharges

    def write_to_excel(self, fName):
        # Delete old record if it exists
        try:
            os.remove("{}.xlsx".format(fName))
        except OSError:
            pass
        # Write to new file
        with pd.ExcelWriter(
                            "{}.xlsx".format(fName),
                            engine='openpyxl',
                            mode='w',
                            ) as writer:
            self.data.to_excel(writer, index=False)

# Functions
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

def excel_to_df(file_name, dbug_lvl):
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

# TODO: Make this less redundant and cursed.
def Household_from_df(
                        df,
                        pv_capacity=PV_CAP_DEFAULT,
                        bess_capacity=BESS_CAP_DEFAULT,
                        bess_soc_min=BESS_SOC_MIN_DEFAULT,
                        bess_soc_init=BESS_SOC_INIT_DEFAULT
    ):
    # Remove any NaNs
    df = df.fillna(0)
    # Split into pandas dataframe for demand and pv
    household = Household(
                            df['PV'].to_numpy(), # Demand
                            df['GC'].to_numpy(),  # PV gen
                            df['CL'].to_numpy(),
                            pv_cap=pv_capacity,
                            bess_capacity=bess_capacity,
                            bess_soc_min=bess_soc_min,
                            bess_soc_init=bess_soc_init,
                            label = 69 # Household number
    )
    household.clean_data()
    return household

"""
# BESS model parameters (user-defined)
bess_capacity = float(input("Enter BESS capacity (kWh): "))   # kWh
bess_min_soc = float(input("Enter minimum SoC (kWh): "))    # kWh (reserve level)
bess_init_soc = float(input("Enter initial SoC (kWh): "))  # kWh (initial state of charge)

# Validate inputs
if bess_capacity <= 0:
    raise ValueError("BESS capacity <= 0")

if bess_soc_min < 0 or bess_min_soc > bess_capacity:
    raise ValueError("Minimum SoC not between 0 and capacity")

if (
    bess_soc_init < bess_soc_min or
    bess_soc_init > bess_capacity
):
    raise ValueError("Initial SoC not between min SoC and capacity")
"""
