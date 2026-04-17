#VPP_model_customer
#To use: import VPP_model_customer as customer
"""
TODO: Code overview
"""

# Imports
import numpy as np
import pandas as pd
from matplotlib import pyplot as plt

# Other python files
import VPP_model_household as house
import VPP_model_NEM as nem

# Classes
class CustomerModel:
    """
    Simple VPP Pricing model (vs. Amber complex)
    Based off the origin pricing structure
    """
    def __init__(
                self,
                price_export_24hr,
                price_import_24hr,
                battery_import_24hr=None,
                price_vpp_use=0.0,
                day_charge=0.0,
                bonus_signup=0.0,
                bonus_monthly=0.0,
                export_max_yr=None,
                soc_min=0.0,
                price_pv_export_threshold=0.0,
                soc_min_flag=False,
                label=None
    ):
        self.priceExport = price_export_24hr
        self.priceImport = price_import_24hr
        if battery_import_24hr != None:
            self.priceImportBattery = self.priceImport
        else:
            self.priceImportBattery = battery_import_24hr
        self.bonusSignup = bonus_signup
        self.bonusMonthly = bonus_monthly
        self.exportMax = export_max_yr
        self.socMin = soc_min
        self.socMinFlag = soc_min_flag

        if np.shape(self.priceExport)[0] > 1:
            print("This plan has a PV export threshold.")
            self.pvThreshold = price_pv_export_threshold

        self.label="no_name"
        if label != None:
            self.label = label

    def __str__(self):
        return "Type: CustomerModel, Name: {}".format(self.label)

# Functions
def model_setup_origin():
    pass

def model_setup_agl():
    pass

def model_setup_globird():
    pass

# Put the Origin VPP price structure into a model

"""
Set based on Victoria Origin Go Variable Solar Boost
TODO: Update to NSW
"""
origin_export_price = np.zeros((24,2))
origin_export_price[:,0] = 0.05 # Flat rate for first 8kWh
origin_export_price[:,1] = 0.01 # Flat rate after 8kWh

origin_import_price = 0.2972*np.ones(24) # Flat rate

origin_vic = CustomerModel(
                    origin_export_price,
                    origin_import_price,
                    price_vpp_use=1.0, # Origin pays $1/kWh for export
                    day_charge=1.2301, # Daily charge
                    bonus_signup=200,
                    export_max_yr=200,
                    soc_min=0.2, # Origin says they will probably leave 20% in the battery
                    soc_min_flag=False, # Origin doesn't let you change the soc min
                    price_pv_export_threshold=8.0,
                    label="Origin Go Variable Solar Boost"
)
print(origin_vic)

"""
Set based on Victoria AGL BYOB
With the battery rewards electricity plan treated as FiT income
"""

agl_export_price = 0.015*np.ones((24,1)) # Flat rate
# Set values between 5pm and 9pm
agl_export_price[17:21,:] = 10/40 # Paid $10 for every 40 kWh exported

# Note: Limit is $400 payout per quarter - not coded!!!
agl_import_price = 0.26741*np.ones(24) # Flat rate

agl_vic = CustomerModel(
                    agl_export_price,
                    agl_import_price,
                    price_vpp_use=1.0, # AGL pays $1 for kWh used in a VPP event.
                    day_charge=1.10704, 
                    bonus_signup=200, # Welcome credit is $200
                    export_max_yr=250,
                    bonus_monthly=float(80/12), # AGL gives annual credit of $80 for VPP participation
                    soc_min=0.2, # AGL says they will probably leave 20% in the battery
                    soc_min_flag=False, # AGL doesn't let you change the soc min
                    label="AGL Bring Your Own Battery"
)
print(agl_vic)

"""
Set based on globird ZEROHERO jemena quote for victoria

    $1 daily bonus for drawing <0.03kWh/hr during 6pm-9pm
    FiT:
    15c for export during 6pm-9pm for first 15kWh
    2c between 4pm-11pm, excluding above
    0c otherwise, excluding above
    $1/kWh FiT during critical peak export event
    
    Consumption:
    0.00c/kWh 11am-2pm
    29.15c/kWh 12am-11am, 2pm-4pm, 11pm-12am
    39.60c/kWh 4pm-11pm
    
    $5c/kWh consumption during critical peak import event
    
    $1.2650/day charge
    
"""
# TODO: Model the daily bonus
# TODO: Model peak import critical event consumption price

globird_export_price = np.zeros((24,2))
# Set price before meeting threshold
globird_export_price[16:23,:] = 0.02
globird_export_price[18:21,0] = 0.15
plt.figure()
plt.plot(np.arange(24), globird_export_price[:,0], '.')
plt.plot(np.arange(24), globird_export_price[:,1], '.')

globird_import_price = np.zeros((24,1))
# Set shoulder prices
globird_import_price[0:11,:] = 0.2915 # 12am-11am
globird_import_price[14:16,:] = 0.2915 #2pm-4pm
globird_import_price[23] = 0.2915 #11pm - 12am
# Set peak prices
globird_import_price[16:23] = 0.3960
plt.figure()
plt.plot(np.arange(24), globird_import_price, '.')

globird_vic = CustomerModel(
                    globird_export_price,
                    globird_import_price,
                    price_vpp_use=1.0, # Globird pays $1 for kWh used in a critical peak export event
                    day_charge=1.2650, 
                    bonus_signup=0, # No welcome credit
                    soc_min=0.0, # No restricitions on minimum battery state of charge, however hardware ususally sets it to 0.2
                    soc_min_flag=False, # Not able to change soc minimmum
                    label="Globird ZEROHERO"
)


# TODO: Generate timeseries arrays for:
    # Export
    # Import

# Using:
    # origin VPP rules
    # Household object
    # Spot price timeseries*


#==========Spot price data==========
spot_data = nem.import_spot_data("nem_spot_data_fy12.xlsx", 0)

# Initial test: Just using only one household
house_data = house.excel_to_df("house_individual_data.xlsx", 0)
# Convert into a household object
household = house.Household_from_df(house_data)
# Combine the demand
household.combine_demand()

# TODO:
# Make minimum state of charge accessible from this level

# Identify times when origin will request battery discharge
    # Maybe look at FCAS contingency events?
    # Otherwise take highest prices

# Calculate total cost including bonuses

# Operation for a 30 min interval
def bess_operation_origin(
                            customer_model,
                            soc_max=0.0,
                            soc_min=0.0,
                            soc_prev=0.0,
                            pv_gen=0.0,
                            demand=0.0,
                            grid_event=False,
                            grid_support_total=0.0,
                            spot_price=0.0
):
        max_grid_support = customer_model.export_max_yr
        charge = 0.0
        discharge = 0.0
        export = 0.0
        grid_support = 0.0
        # Net energy balance (kWh over 30 min)
        net_demand = demand - pv_gen
        available_capacity = soc_max - soc_prev
        available_energy = soc_prev - soc_min

        # Self consumption and PV export to grid.
        # In grid event, all available PV is exported
        # Case 1: Still demand after PV gen used
        if net_demand > 0:
            # Discharge to meet remaining demand,
            # Using available bess capacity
            discharge = min(net_demand, available_capacity)
            # Update remaining demand and capacity
            net_demand = net_demand - discharge
            available_capacity = available_capacity - discharge
            if net_demand > 0: # Still remaining demand
                export = -net_demand # Need to import electricity
        # Case 2: Negative demand: Have excess PV Gen
        elif net_demand < 0:
            if (grid_event and
                grid_support_total < max_grid_support
                ):
                # Export any PV to the grid
                max_export = max_grid_support - grid_support_total
                grid_support = min(-net_demand, max_export)
                export = export + grid_support
            else:
                # Charge battery til PV gen runs out or full
                if -net_demand > available_energy:
                    # Charge battery til full
                    charge = max(available_energy, 0)
                    # Export any leftover
                    export = -net_demand - available_energy
                else:
                    # Charge battery til PV gen runs out
                    charge = -net_demand
                    # No export
        # If grid event, discharge battery into grid
        # Include any PV export
        grid_support_total = grid_support_total + grid_support
        if(
            export >=0.0 and # Can't export if drawing from grid
            grid_event and
            grid_support_total < max_grid_support
        ):
            max_export = max_grid_support - grid_support_total
            discharge_to_grid = min(available_energy, max_export)
            # Update discharge so SoC is accurate
            discharge = discharge + discharge_to_grid
            # Update grid support. include any PV export
            grid_support = grid_support + discharge_to_grid
            export = export + discharge_to_grid

        soc = soc_prev + charge - discharge # Update SoC
        # Enforce bounds (safety check)
        # TODO: Print message if any bounds exceeded.
        soc = min(soc, soc_max)
        soc = max(soc, soc_min)
        return [charge, discharge, soc, export, grid_support]

# Function looping over whole year
def calc_bess_data_origin(household, customer_model, spot_data):
    n = len(household.data.index)
    soc = np.zeros(n)            # State of Charge (kWh)
    charge = np.zeros(n)         # Charging energy (kWh)
    discharge = np.zeros(n)      # Discharging energy (kWh)
    export = np.zeros(n)
    grid_support = np.zeros(n)

    # Set initial SoC
    soc[0] = household.bessSocInit

    # BESS operation loop
    grid_support_total = 0.0
    for t in range(1, n):
        # TODO: Identify it is a grid event
        # Can use FCAS or spot price data
        grid_event = False
        bess_data = bess_operation_origin(
                                customer_model,
                                soc_min=household.bessCapacity,
                                soc_max=household.bessSocMin,
                                soc_prev=soc[t-1],
                                pv_gen=household.data['PV'].iloc[t],
                                demand=household.data['PV'].iloc[t],
                                spot_price=spot_data.iloc[t],
                                grid_event=grid_event,
                                grid_support_total=grid_support_total
        )
        charge[t] = bess_data[0]
        discharge[t] = bess_data[1]
        soc[t] = bess_data[2]
        export[t] = bess_data[3]
        grid_support[t] = bess_data[4]
        grid_support_total = grid_support_total + grid_support[t]

    # Append BESS data to dataframe
    household.data['BESS SoC (kWh)'] = soc   # State of Charge
    household.data['BESS Charge (kWh)'] = charge # kWh charges
    household.data['BESS Discharge (kWh)'] = discharge # kWh discharges
