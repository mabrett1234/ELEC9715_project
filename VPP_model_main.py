#VPP_model_main
# Main - High level code

# Libraries
import numpy as np
import pandas as pd
import os
from matplotlib import pyplot as plt

# Other python files
import VPP_model_household as house

#==========Main==========

#==========Individual household==========

# Initial test: Just using only one household
house_data = house.import_household_data("vic_house_data.xlsx", 2)

# Convert into a household object
household = house.Household_from_df(house_data)

# Combine the demand
household.combine_demand()

# Calculate the bess data
household.calc_bess_data()

# Write the data to excel
household.write_to_excel("vic_house_data_with_bess")
