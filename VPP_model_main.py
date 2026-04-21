#VPP_model_main
# Main - High level code

# Libraries
import numpy as np
import pandas as pd
import os
from matplotlib import pyplot as plt

# Other python files
import VPP_model_household as house
import VPP_model_NEM as nem
import VPP_model_customer as customer
import VPP_origin as origin

#==========Main==========

#==========Individual household==========
def run_model_individual(
                            retailer = origin.model_setup(),
                            spot_data = None,
                            grid_event_arr = None,
                            ref_num=69,
                            house_data=None,
                            input_dir='dataIn',
                            output_dir='dataOut'
):
    # Convert into a household object
    household = house.Household_from_df(
                                        house_data,
                                        pv_capacity=6.0,#kW
                                        bess_capacity=30.0,#kWh
                                        bess_soc_min=(30.0*0.2),
                                        bess_soc_init=30.0
    )
    # Make another that will do self consumption operation
    household_noVPP = house.Household_from_df(
                                        house_data,
                                        pv_capacity=6.0,#kW
                                        bess_capacity=30.0,#kWh
                                        bess_soc_min=(30.0*0.2),
                                        bess_soc_init=30.0
    )
    # Update household bess params based on retailer
    household.bessSocMin = household.bessCapacity*retailer.socMin
    household_noVPP.bessSocMin = household.bessSocMin

    #=========Self consumption behaviour=========
    # Calculate the bess data for self consumption
    household_noVPP.calc_bess_data()
    # Calculate the cost for origin plan
    origin.calc_cost(retailer, household_noVPP, baseline_flag=True)
    # Add the spot data in there too
    nem.calc_cost(household_noVPP, spot_data)
    # Save data to excel spreadsheet
    fname = "{}\\self_consume_{}".format(output_dir, ref_num)
    household.write_to_excel(fname)

    #=========VPP behaviour=========
    # Calculate the bess operation over the year
    origin.calc_bess_data(
                            household,
                            origin_model,
                            grid_event_arr
    )
    # Work out export and import
    house.split_export(household)
    # Calculate the bill
    origin.calc_cost(origin_model, household, baseline_flag=False)
    # Add the spot data there too
    nem.calc_cost(household, spot_data)
    # Save data to excel spreadsheet
    fname = "{}\\origin_vpp_{}".format(output_dir, ref_num)
    household.write_to_excel(fname)

#==========Many households==========
# Put any code that will be repeated here:
#==========Spot price data==========
# Import the spot price data
spot_data = nem.import_spot_data("nem_spot_data_fy12.xlsx", 0)
# Identify time periods when spot price is very high.
# Using 15 as the number of events
n_events = 200
grid_events = nem.identify_grid_events(spot_data, n_events)

#========Origin setup========
# Make a class with origin info
origin_model = origin.model_setup()
print(origin_model) # print to check
# Update the bess minimum state of charge to match origin VPP rules


#=====Household data=========

# Import the full household data
print("Importing household data. This may take some time.")
df = house.excel_to_df("household_data_clean.xlsx", 0)
t = pd.to_datetime(df.iloc[:, 0])
df = df.set_index(t)
df = df.iloc[:, 1:]
print("Data imported.")

n = int(len(df.columns)/3)
# TO DO: Save useful annual data totals to dataframe and then excel file.
# TO DO: Check the cost calc is correct for export with self consumption op
# TO DO: Save timeseries totals to dataframe and then excel file.
for i in range(0, n):
    # Get current household
    df_curr = df.iloc[:,(i*3):((i+1)*3)]
    ref_num = str(df_curr.columns[0])
    ref_num = int(ref_num.split("_")[0])
    # Update columns for readability
    old_cols = df_curr.columns
    df_curr.columns = ['CL', 'GC', 'PV']
    print("======FOR HOUSEHOLD {}=======".format(ref_num))
    run_model_individual(
                        retailer = origin_model,
                        spot_data = spot_data,
                        grid_event_arr = grid_events,
                        ref_num=ref_num,
                        house_data=df_curr,
                        input_dir='dataIn',
                        output_dir='dataOut'
    )

