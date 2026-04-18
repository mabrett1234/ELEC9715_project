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

# Main code
