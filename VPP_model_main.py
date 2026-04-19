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

# Initial test: Just using only one household
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
# Calculate the bess data
household.calc_bess_data()
# Write the data to excel
household.write_to_excel("house_individual_data_w_bess")

#==========Spot price data==========
# Import the spot price data
spot_data = nem.import_spot_data("nem_spot_data_fy12.xlsx", 0)
# Identify time periods when spot price is very high.
# Using 15 as the number of events
grid_events = nem.identify_grid_events(spot_data, 15)

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
# Calculate the bill
origin_profit = origin.calc_cost(
                                    origin_model,
                                    household,
                                    first_yr=False
)
# Print the total bill to terminal
print("Bill for FY 2012 - 2013 for origin VPP was", end="")
print(" ${:.2f}.".format(-origin_profit))
# Write to excel
household.write_to_excel("household_individual_origin_vpp")
