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

# Classes and methods

# Functions
def import_spot_data(fName, dbug_lvl):
    # Use function from household module
    df_spot = house.excel_to_df(fName, 0)
    # Rename columns
    df_spot.columns = ['time', 'spot price']
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
    print("{} grid events".format(count))
    print("Spot price threshold = ${:.2f}/MWh".format(threshold))
    for t in range(0, n):
        if spot_data.iloc[t] > threshold:
            df.iloc[t,0] = 1
    return df

# TODO: Update origin costing to look like this
def calc_cost(
                household,
                spot_data
):
    n = len(household.data.index)
    #====Revenue calcs====
    # Revenue from export
    export_arr = household.data['Export (kWh)'].to_numpy()
    price_arr = spot_data.to_numpy()/1000 # Scale to kWh
    revenue_export_arr = np.zeros(n)
    import_arr = household.data['Import (kWh)'].to_numpy()
    cost_import_arr = np.zeros(n)
    # Loop through by 30 min step
    for t in range(0, n):
        revenue_30min = price_arr[t]*export_arr[t] / 2
        revenue_export_arr[t] = revenue_30min
        cost_30min = price_arr[t]*import_arr[t] / 2
        cost_import_arr[t] = cost_30min
    # Update the data frame
    profit_spot_arr = revenue_export_arr - cost_import_arr
    household.data['Spot Price ($/kWh)'] = price_arr
    household.data['Spot Revenue ($)'] = revenue_export_arr
    household.data['Spot Cost ($)'] = cost_import_arr
    household.data['Spot Profit ($)'] = profit_spot_arr
    print("Total Spot Profit = ", end = "")
    print("${:.2f}/yr".format(profit_spot_arr.sum()))
