#VPP_model_NEM
#To use: import VPP_model_NEM as nem
"""
This code handles spot price data.
Imports for the same timeframe as household data.
2012-2013 FY
Start: 2012-07-01 00:30:00
End: 2013-07-01 00:00:00
Converts to useful format - pandas dataframe.
"""

# Imports
import numpy as np
import pandas as pd
from matplotlib import pyplot as plt

# Other libraries
import VPP_model_household as house
import VPP_model_customer as customer
import VPP_origin as origin

# Classes and methods

# Functions
def import_spot_data(fName, dbug_lvl):
    # Use function from household module
    df_spot = house.excel_to_df(fName, 0)
    # Rename columns
    df_spot.columns = ['time', 'spot price']
    if dbug_lvl > 1: print(df_spot)
    # Set time as index to make a neat time series dataframe
    t = pd.to_datetime(df_spot['time'])
    df_spot = df_spot.set_index(t)
    df_spot = df_spot['spot price'] # Make one column
    if dbug_lvl > 0: print(df_spot)
    return df_spot

def identify_grid_events(spot_data, n_events):
    n = len(spot_data.index)
    df = pd.DataFrame(
                        {"grid event":np.zeros(n)},
                        index = spot_data.index
    )
    
    # Work out correct threshold
    mean = spot_data.mean()
    std_dev = spot_data.std()
    print("Mean = ${:.2f}/MWh".format(mean))
    print("StdDev = ${:.2f}/MWh".format(std_dev))
    count = 0
    threshold = mean
    for i in range(0, 30):
        count = (spot_data > threshold).sum()
        if count > (n_events - 1):
            threshold = mean + std_dev*i
    # Just t
    print("{} grid events".format(count))
    print("Spot price threshold = ${:.2f}/MWh".format(threshold))
    for t in range(0, n):
        if spot_data.iloc[t] > threshold:
            df.iloc[t,0] = 1
    return df

# TODO: Update origin costing to look like this
# Using spot data
def calc_cost(
                household,
                spot_data
):
    # Initialise annual totals
    revenue_yr = 0.0
    cost_yr = 0.0
    profit_yr = 0.0
    n = len(household.data.index)
    #====Revenue calcs====
    # Revenue from export
    export_arr = household.data['Export (kWh)'].to_numpy()
    price_arr = spot_data.to_numpy()/1000 # Scale to kWh
    revenue_export_arr = np.zeros(n)
    import_arr = household.data['Import (kWh)'].to_numpy()
    cost_import_arr = np.zeros(n)
    # Loop through by days
    for t in range(0, n):
        revenue_30min = price_arr[t]*export_arr[t] / 2
        revenue_export_arr[t] = revenue_30min
        cost_30min = price_arr[t]*import_arr[t]
        cost_30min = cost_30min / 2
        cost_import_arr[t] = cost_30min
    # Update the total cost
    revenue_yr = revenue_yr + np.sum(revenue_export_arr)
    cost_yr = cost_yr + np.sum(cost_import_arr)
    # Update the data frame
    household.data['Export Revenue ($)'] = revenue_export_arr
    household.data['Import Cost ($)'] = cost_import_arr
    household.data['Total Cost ($)'] = revenue_export_arr - cost_import_arr
    #====Profit calcs====
    profit_yr = revenue_yr - cost_yr
    return float(profit_yr)

# Main code - testing

house_data = house.excel_to_df("house_individual_data.xlsx", 0)
# Convert into a household object
household = house.Household_from_df(
                                    house_data,
                                    pv_capacity=6.0,#kW
                                    bess_capacity=30.0,#kWh
                                    bess_soc_min=(30.0*0.2),
                                    bess_soc_init=30.0
)
# Combine the demand
household.combine_demand()
#==========Spot price data==========
# Import the spot price data
spot_data = import_spot_data("nem_spot_data_fy12.xlsx", 0)
# Identify time periods when spot price is very high.
# Using 15 as the number of events
grid_events = identify_grid_events(spot_data, 15)

#========VPP cost: Origin========
# Make a class with origin info
origin_model = origin.model_setup()
print(origin_model) # print to check
# Update the bess minimum state of charge to match origin VPP rules
household.bessSocMin = household.bessCapacity*origin_model.socMin
# Calculate the bess operation over the year
origin.calc_bess_data(
                        household,
                        origin_model,
                        spot_data,
                        grid_events
)
# Work out export and import
house.split_export(household)

# Calculate the bill
"""
origin_profit = origin.calc_cost(
                                    origin_model,
                                    household,
                                    first_yr=False
)
"""
# Print the total bill to terminal
#print("Bill for FY 2012 - 2013 for origin VPP was", end="")
#print(" ${:.2f}.".format(-origin_profit))
# Write to excel
#household.write_to_excel("household_individual_origin_vpp")

#=========VPP cost: spot market=========
calc_cost(household, spot_data)
