#VPP_origin.py

"""
TODO: Code description
"""

# Libraries
import numpy as np
import pandas as pd
import os
from matplotlib import pyplot as plt

# Other python files
import VPP_model_household as house
import VPP_model_customer as customer

# Functions

#====Functions for VPP operation calcs====
# TODO (non urgent): Really confusing use of 
# capacity, SoC, kW vs. kWh
# Could clean up to be more explicit and less likely
# For errors
def bess_operation(
                            customer_model,
                            soc_max=0.0,
                            soc_min=0.0,
                            soc_prev=0.0,
                            pv_gen=0.0,
                            demand=0.0,
                            grid_event=False,
                            grid_support_total=0.0,
                            dbug_lvl=0
):
    """
    USING ORIGIN MODEL OF VPP
    This function decides bess operation over a 30min interval.
    """
    max_grid_support = customer_model.exportMax
    charge = 0.0
    discharge = 0.0
    export = 0.0
    grid_support = 0.0
    # Net energy balance (kWh over 30 min)
    net_demand = demand - pv_gen
    charge_max = soc_max - soc_prev # Available capacity to charge
    discharge_max = soc_prev - soc_min # Available energy to discharge
    if dbug_lvl > 1:
        print("Demand before PV Gen = {:.2f} kWh".format(demand))
        print("after = {:.2f} kWh".format(net_demand))
    # Self consumption and PV export to grid.
    # In grid event, all available PV is exported
    # Case 1: Still demand after PV gen used
    if net_demand > 0:
        # Discharge to meet remaining demand,
        # Using available bess capacity
        discharge = min(net_demand, discharge_max)
        # Update remaining demand and energy
        net_demand = net_demand - discharge
        discharge_max = discharge_max - discharge
        if net_demand > 0: # Still remaining demand
            export = -net_demand # Need to import electricity
    # Case 2: Negative demand: Have excess PV Gen
    elif net_demand < 0:
        if (grid_event and
            grid_support_total < max_grid_support
        ):
            # Export any PV to the grid
            if dbug_lvl > 0:
                print("Grid event: Exporting excess PV gen.")
            max_export = max_grid_support - grid_support_total
            grid_support = min(-net_demand, max_export)
            export = export + grid_support
        else:
            # Charge battery til PV gen runs out or full
            if -net_demand > charge_max:
                # Charge battery til full
                charge = charge_max
                # Export any leftover
                export = -net_demand + charge
                if dbug_lvl > 1:
                    print("Charging battery until full.")
            else:
                # Charge battery til PV gen runs out
                charge = -net_demand
                if dbug_lvl > 1:
                    print("Charging battery with remaining PV generation")
                    print("charging battery {} kWh".format(charge))
            charge_max = charge_max - charge
    # If grid event, discharge battery into grid
    # Include any PV export
    grid_support_total = grid_support_total + grid_support
    if (
        export >=0.0 and # Can't export if drawing from grid
        grid_event and
        grid_support_total < max_grid_support
    ):
        if dbug_lvl > 0:
            print("Grid event: discharging battery into grid.")
        max_export = max_grid_support - grid_support_total
        discharge_to_grid = min(discharge_max, max_export)
        # Update discharge so SoC is accurate
        discharge = discharge + discharge_to_grid
        discharge_max = discharge_max - discharge_to_grid
        # Update grid support. include any PV export
        grid_support = grid_support + discharge_to_grid
        export = export + discharge_to_grid

    soc = soc_prev + charge - discharge # Update SoC
    # Enforce bounds (safety check)
    # TODO: Print message if any bounds exceeded.
    #soc = min(soc, soc_max)
    #soc = max(soc, soc_min)
    if dbug_lvl > 1 and export > 0.0:
        print("OMG EXPORTING TO THE GRID YAYAYAYAY")
    elif dbug_lvl > 1 and export < 0.0:
        print("ughhh have to import from the grid")
    return [charge, discharge, soc, export, grid_support]

# Function looping over whole year
def calc_bess_data(
                    household,
                    customer_model,
                    grid_events
):
    print("Calculating VPP household operation")
    n = len(household.data.index)
    soc = np.zeros(n)            # State of Charge (kWh)
    charge = np.zeros(n)         # Charging energy (kWh)
    discharge = np.zeros(n)      # Discharging energy (kWh)
    export = np.zeros(n)         # Exported energy (kWh)
    grid_support = np.zeros(n)   # Grid support (kWh)
    # Set initial SoC
    soc[0] = household.bessSocInit
    # BESS operation loop
    grid_support_total = 0.0
    for t in range(1, n):
        grid_event_flag = False
        if grid_events.iloc[t,0] == 1:
            grid_event_flag = True
        bess_data = bess_operation(
                                customer_model,
                                soc_min=household.bessSocMin,
                                soc_max=household.bessCapacity,
                                soc_prev=soc[t-1],
                                pv_gen=household.data['PV'].iloc[t],
                                demand=household.data['load'].iloc[t],
                                grid_event=grid_event_flag,
                                grid_support_total=grid_support_total
        )
        # Update array values - could clean up by using a class
        charge[t] = bess_data[0]
        discharge[t] = bess_data[1]
        soc[t] = bess_data[2]
        export[t] = bess_data[3]
        grid_support[t] = bess_data[4]
        # Update grid support total
        grid_support_total = grid_support_total + grid_support[t]
        if grid_event_flag:
            print("Grid event: ", end = "")
            print("Exported {:.2f} kWh".format(grid_support[t]))
            print("total = {:.2f}".format(grid_support_total))

    # Append BESS data to dataframe
    household.data['SoC (kWh)'] = soc   # State of Charge
    household.data['Charge (kWh)'] = charge # kWh charges
    household.data['Discharge (kWh)'] = discharge # kWh discharges
    household.data['Export (kWh)'] = export
    household.data['Grid Support (kWh)'] = grid_support
    household.split_export()
    print("Grid event total = {:.2f} kWh".format(grid_support_total))

def calc_cost(
                customer_model,
                household,
                baseline_flag=True
):
    n = len(household.data.index)
    if baseline_flag == True:
        household.data['Grid Support (kWh)'] = np.zeros(n)
    #==Revenue from grid support==
    grid_supp_arr = household.data['Grid Support (kWh)'].to_numpy()
    rev_grid_supp_arr = customer_model.price_vpp_use*grid_supp_arr
    #==Revenue from export and import==
    # Get rid of any export for grid support
    # otherwise double counted
    household.data['Self Export (kWh)'] = household.data['Export (kWh)'] - household.data['Grid Support (kWh)']
    # Make some arrays
    # For export calcs
    export_arr = household.data['Self Export (kWh)']
    rev_export_arr = np.zeros(n)
    # For import calcs
    import_arr = household.data['Import (kWh)'].to_numpy()
    cost_import_arr = np.zeros(n)
    # Export limit - defines pricing
    day_export_lim = customer_model.pvThreshold
    # Loop through arrays in days
    for day in range(0, 365):
        export_day_tot = 0.0 # Used for Export cap.
        # Loop through day in 30min step
        for t in range(0, 48):
            price_ex_30min = customer_model.priceExport[int(t/2), 0]
            price_im_30min = customer_model.priceImport[int(t/2)]
            if export_day_tot > day_export_lim:
                price_ex_30min = customer_model.priceExport[int(t/2), 1]
            # Calculate 30min revenue
            rev_export_arr[day*t] = export_arr[day*t]*price_ex_30min/2
            # Calculate 30min cost
            cost_import_arr[day*t] = import_arr[day*t]*price_im_30min/2
            # Update totals
            export_day_tot = export_day_tot + export_arr[day*t]

    #====Cost calcs====
    # Daily fees
    daily_fee_arr = np.zeros(n)
    for i in range(0, n):
        if i % 48 == 0:
            daily_fee_arr[i] = customer_model.chargeDay

    #====Save data to data frame====
    cost_tot_arr = daily_fee_arr + cost_import_arr
    rev_tot_arr = rev_grid_supp_arr + rev_export_arr
    profit_tot_arr = rev_tot_arr - cost_tot_arr
    household.data['Export Revenue ($)'] = rev_export_arr
    household.data['Grid Support Revenue ($)'] = rev_grid_supp_arr
    household.data['Import Cost ($)'] = cost_import_arr
    household.data['Daily fee cost ($)'] = daily_fee_arr
    household.data['Total Cost ($)'] = cost_tot_arr
    household.data['Total Revenue ($)'] = rev_tot_arr
    household.data['Total Profit ($)'] = profit_tot_arr
    print("Total Profit = ${:.2f}/yr".format(profit_tot_arr.sum()))

def model_setup():
    # Put the Origin VPP price structure into a model
    """
    Set based on Victoria Origin Go Variable Solar Boost
    TODO: Update to NSW
    """
    origin_export_price = np.zeros((24,2))
    origin_export_price[:,0] = 0.05 # Flat rate for first 8kWh
    origin_export_price[:,1] = 0.01 # Flat rate after 8kWh

    origin_import_price = 0.2972*np.ones(24) # Flat rate

    ret = customer.CustomerModel(
                        origin_export_price,
                        origin_import_price,
                        price_vpp_use=1.0, #$1/kWh for grid support
                        day_charge=1.2301, # Daily charge
                        bonus_signup=200,
                        export_max_yr=200,# Max grid support
                        soc_min=0.2, # Say they leave 20% charge
                        soc_min_flag=False, # Can't change the soc min
                        price_pv_export_threshold=8.0,
                        label="Origin Go Variable Solar Boost"
    )
    return ret

