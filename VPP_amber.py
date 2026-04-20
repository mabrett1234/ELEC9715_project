#VPP_model_customer
#To use: import VPP_model_customer as customer
"""
TODO: Code overview
"""

# Imports
import numpy as np
import pandas as pd
from matplotlib import pyplot as plt


# Copy of the origin functions
def bess_operation(
                            customer_model,
                            soc_max=0.0,
                            soc_min=0.0,
                            soc_prev=0.0,
                            pv_gen=0.0,
                            demand=0.0,
                            grid_event=False,
                            grid_support_total=0.0,
                            spot_price=0.0,
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
                            spot_data,
):
    n = len(household.data.index)
    soc = np.zeros(n)            # State of Charge (kWh)
    charge = np.zeros(n)         # Charging energy (kWh)
    discharge = np.zeros(n)      # Discharging energy (kWh)
    export = np.zeros(n)
    # Set initial SoC
    soc[0] = household.bessSocInit

    # BESS operation loop
    for t in range(1, n):
        bess_data = bess_operation(
                                customer_model,
                                soc_min=household.bessSocMin,
                                soc_max=household.bessCapacity,
                                soc_prev=soc[t-1],
                                pv_gen=household.data['PV'].iloc[t],
                                demand=household.data['load'].iloc[t],
                                spot_price=spot_data.iloc[t],
        )
        charge[t] = bess_data[0]
        discharge[t] = bess_data[1]
        soc[t] = bess_data[2]
        export[t] = bess_data[3]

    # Append BESS data to dataframe
    household.data['SoC (kWh)'] = soc   # State of Charge
    household.data['Charge (kWh)'] = charge # kWh charges
    household.data['Discharge (kWh)'] = discharge # kWh discharges
    household.data['Export (kWh)'] = export

def split_export(household):
    # Split export into positive and negative arrays
    # Move this to a method within the household class
    household.data['Import (kWh)'] = -household.data['Export (kWh)']
    household.data['Import (kWh)'] = household.data['Import (kWh)'].clip(0)
    household.data['Export (kWh)'] = household.data['Export (kWh)'].clip(0)

def calc_cost(
                customer_model,
                household
):
    revenue_yr = 0.0
    cost_yr = 0.0
    profit_yr = 0.0
    n = len(household.data.index)

    #====Revenue calcs====
    # Revenue from export
#TODO: Update to calculate from spot price
    # Loop through the dataframe by days
    day_export_lim = customer_model.pvThreshold
    export_yr = household.data['Export (kWh)']
    #print(export_yr)
    revenue_export = 0.0
    for day in range(0, 365):
        offset = day*24
        export_day = export_yr.iloc[offset:(offset+24)]
        # Loop through by hour
        revenue_day = 0.0
        export_day_tot = 0.0
        for hr in range(0, 24):
            price = customer_model.priceExport[hr, 0]
            if export_day_tot > day_export_lim:
                price = customer_model.priceExport[hr, 1]
            # Calculate hourly revenue
            export_hr = export_day.iloc[hr*2:(hr*2+1)].sum()
            revenue_hr = price*export_hr
            # Update totals
            revenue_day = revenue_day + revenue_hr
            export_day_tot = export_day_tot + export_hr
        revenue_export = revenue_export + revenue_day
    print("Revenue from export = ${:.2f}/yr".format(revenue_export))
    # Revenue from any bonuses
    # Origin just gives a one-off sign up bonus
    revenue_bonus = 0.0
    if first_yr:
        revenue_bonus = revenue_bonus + customer_model.bonusSignup
    # No monthly bonus for Origin, below is for later code
    revenue_bonus = revenue_bonus + 12*customer_model.bonusMonthly

    #====Cost calcs====
    # Daily or monthly fees
    # In object creation these are zero by default
    daily_fees = 365*customer_model.chargeDay
    monthly_fees = 12*customer_model.chargeMonth
    # Update total cost
    cost_yr = cost_yr + daily_fees + monthly_fees

    # Cost from imports
#TODO: Update to calculate from spot price
    import_yr = household.data['Import (kWh)']
    import_day_tot = 0.0
    cost_import = 0.0
    cost_day = 0.0
    for day in range(0, 365):
        offset = day*24
        import_day = import_yr.iloc[offset:(offset+24)]
        # Loop through by hour
        cost_day = 0.0
        import_day_tot = 0.0
        for hr in range(0, 24):
            price = customer_model.priceImport[hr]
            # Calculate hourly cost
            import_hr = import_day.iloc[hr*2:(hr*2+1)].sum()
            cost_hr = price*import_hr
            # Update totals
            cost_day = cost_day + cost_hr
            import_day_tot = import_day_tot + import_hr
        cost_import = cost_import + cost_day
    print("Cost from import = ${:.2f}/yr".format(cost_import))
    cost_yr = cost_yr + cost_import
    #====Profit calcs====
    profit_yr = revenue_yr - cost_yr
    print(profit_yr)
    return float(profit_yr)

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
