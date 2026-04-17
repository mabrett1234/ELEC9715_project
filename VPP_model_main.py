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

#==========Main==========

#==========Individual household==========

# Initial test: Just using only one household
house_data = house.excel_to_df("house_individual_data.xlsx", 0)

# Convert into a household object
household = house.Household_from_df(house_data)

# Combine the demand
household.combine_demand()

# Calculate the bess data
household.calc_bess_data()

# Write the data to excel
household.write_to_excel("house_individual_data_w_bess")

#==========Spot price data==========
spot_data = nem.import_spot_data("nem_spot_data_fy12.xlsx", 0)
