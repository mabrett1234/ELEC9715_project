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
    annual_totals = np.zeros(6)

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
        print("Creating household class...")
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
        self.combine_demand()
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
        print("Combining CL and GC into total demand")
        self.data['load'] = self.data['GC'] + self.data['CL']

    def split_export(self):
        # Split export into positive and negative arrays
        print("Splitting net export into +ve import and export")
        self.data['Import (kWh)'] = -self.data['Export (kWh)']
        self.data['Import (kWh)'] = self.data['Import (kWh)'].clip(0)
        self.data['Export (kWh)'] = self.data['Export (kWh)'].clip(0)
    
    def calc_bess_data(self):
        print("Calculating self consumption bess operation")
        n = len(self.data.index)
        soc = np.zeros(n)            # State of Charge (kWh)
        charge = np.zeros(n)         # Charging energy (kWh)
        discharge = np.zeros(n)      # Discharging energy (kWh)
        export = np.zeros(n)         # Exported energy (kWh)
        # Set initial SoC
        soc[0] = self.bessSocInit
        # BESS operation loop
        for t in range(1, n):
            # Net energy balance (kWh over 30 min)
            # This is generation!
            net_energy = self.data['PV'].iloc[t] - self.data['load'].iloc[t]

            # Case 1: Excess PV -> charge BESS
            available_capacity = self.bessCapacity - soc[t-1]
            available_energy = soc[t-1] - self.bessSocMin
            # all elements set to zero already

            # Case 1: Excess PV -> charge BESS
            if net_energy > 0:
                charge[t] = min(net_energy, available_capacity)
                # Update remaining generation
                net_energy = net_energy - charge[t]
                # TODO: Calculate export
            # Case 2: Not enough PV -> discharge BESS
            elif net_energy < 0:
                discharge[t] = min(
                                    -net_energy,
                                max(available_energy, 0)
                )
                # Update remaining generation
                # Will be zero if bess meets demand
                # Otherwise negative
                net_energy = net_energy + discharge[t]
            # Update export
            export[t] = net_energy
            # Update SoC
            soc[t] = soc[t-1] + charge[t] - discharge[t]

        # Append BESS data to dataframe
        self.data['SoC (kWh)'] = soc   # State of Charge
        self.data['BESS Charge (kWh)'] = charge # kWh charges
        self.data['BESS Discharge (kWh)'] = discharge # kWh discharges
        self.data['Export (kWh)'] = export

    def calc_totals(self, ref_num):
        # Can only be called after the calc cost in origin ting
        print("Calculating annual totals.")
        self.annual_totals[0] = ref_num
        self.annual_totals[1] = self.data['Export (kWh)'].sum()
        self.annual_totals[2] = self.data['Import (kWh)'].sum()
        self.annual_totals[3] = self.data['Grid Support (kWh)'].sum()
        self.annual_totals[4] = self.data['Total Profit ($)'].sum()
        self.annual_totals[5] = self.data['Spot Profit ($)'].sum()

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

