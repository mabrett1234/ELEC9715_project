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
import VPP_model_NEM as nem
import VPP_model_customer as customer

# Functions

#====Functions for VPP operation calcs====

def model_setup():
    """
    Set based on Victoria AGL BYOB
    With the battery rewards electricity plan treated as FiT income
    """

    agl_export_price = 0.015*np.ones((24,1)) # Flat rate
    # Set values between 5pm and 9pm
    agl_export_price[17:21,:] = 10/40 # $10 for every 40 kWh exported
    # Note: Limit is $400 payout per quarter - not coded!!!
    agl_import_price = 0.26741*np.ones(24) # Flat rate

    ret = customer.CustomerModel(
                        agl_export_price,
                        agl_import_price,
                        price_vpp_use=1.0, # pay $1/kWh grid support
                        day_charge=1.10704,
                        bonus_signup=200, 
                        export_max_yr=250,
                        bonus_monthly=float(80/12), #$80/yr credit
                        soc_min=0.2, # Says they leave 20% charge
                        soc_min_flag=False, # Can't change soc min.
                        label="AGL Bring Your Own Battery"
    )
    return ret

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
    pass


def calc_bess_data(
                            household,
                            customer_model,
                            spot_data,
                            grid_events
):
    pass


def calc_cost(
                        customer_model,
                        household,
                        first_yr=True
):
    return 0.0
