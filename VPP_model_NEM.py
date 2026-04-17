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

# Main code
