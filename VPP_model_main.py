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
def run_model_individual(household_num, input_dir, output_dir):
    #==Initial test: Just using only one household
    # Import house data into a dataframe
    fname = "{}\\house_data_{}.xlsx".format(input_dir, household_num)
    house_data = house.excel_to_df(fname, 0)
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
    household.bessSocMin = household.bessCapacity*origin_model.socMin
    household_noVPP.bessSocMin = household.bessSocMin

    #=========Self consumption behaviour=========
    # Calculate the bess data for self consumption
    household_noVPP.calc_bess_data()
    # Calculate the cost for origin plan
    origin.calc_cost(origin_model, household_noVPP, baseline_flag=True)
    # Add the spot data in there too
    nem.calc_cost(household_noVPP, spot_data)
    # Save data to excel spreadsheet
    fname = "{}\\self_consume_{}".format(output_dir, household_num)
    household.write_to_excel(fname)

    #=========VPP behaviour=========
    # Calculate the bess operation over the year
    origin.calc_bess_data(
                            household,
                            origin_model,
                            grid_events
    )
    # Work out export and import
    house.split_export(household)
    # Calculate the bill
    origin.calc_cost(origin_model, household, baseline_flag=False)
    # Add the spot data there too
    nem.calc_cost(household, spot_data)
    # Save data to excel spreadsheet
    fname = "{}\\origin_vpp_{}".format(output_dir, household_num)
    household.write_to_excel(fname)

#==========Many households==========
# First go: Minimal changes to individual code
run_model_individual(69, 'dataIn', 'dataOut')
