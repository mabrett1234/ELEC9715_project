#clean_data

# Imports
import numpy as np
import pandas as pd
from matplotlib import pyplot as plt

# Other libraries
import VPP_model_household as house

# Import the full household data
print("Importing household data. This may take some time.")
df = house.excel_to_df("household_data_full.xlsx", 0)
t = pd.to_datetime(df.iloc[:, 0])
df = df.set_index(t)
df = df.iloc[:, 1:]
print("Data imported.")
print(df.columns)

# Loop through the models?
n = int(len(df.columns)/3)
print("n = {}".format(n))
invalid_refs = []
all_refs = []
invalid_cols = []
for i in range(0, n):
    # Get current household
    df_curr = df.iloc[:,(i*3):((i+1)*3)]
    ref_num = str(df_curr.columns[0])
    ref_num = ref_num.split("_")[0]
    # Update columns for readability
    old_cols = df_curr.columns
    df_curr.columns = ['CL', 'GC', 'PV']
    print("Reference number = {}".format(ref_num))
    all_refs.append(ref_num)
    # Check if demand is valid
    valid = True
    day = 0
    demand_arr = df_curr['GC'].to_numpy()
    pv_arr = df_curr['PV'].to_numpy()
    while(valid and day < 365):
        demand_day = demand_arr[day*48:(day+1)*48]
        pv_day = pv_arr[day*48:(day+1)*48]
        if demand_day.sum() < 0.05:
            valid = False
            print("Household {} has invalid demand data".format(ref_num))
            print("timestamp: day = {}".format(day))
        elif pv_day.sum() < 0.05:
            valid = False
            print("Household {} has invalid PV data.".format(ref_num))
            print("timestamp: day = {}".format(day))
        day = day + 1
    if valid == False:
        invalid_refs.append(ref_num)
        # Drop from the main data frame
        invalid_cols.append(old_cols)

for cols in invalid_cols:
    df.drop(cols, axis=1, inplace=True)
print("Invalid Reference numbers:")
print(invalid_refs)

print("Writing clean data to excel file. This may take some time.")
df.to_excel("household_data_clean.xlsx")
print("Written data to excel.")



