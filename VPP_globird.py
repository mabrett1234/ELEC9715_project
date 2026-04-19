#VPP_globird.py

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

    export_price = np.zeros((24,2))
    # Set price before meeting threshold
    export_price[16:23,:] = 0.02
    export_price[18:21,0] = 0.15

    import_price = np.zeros((24,1))
    # Set shoulder prices
    import_price[0:11,:] = 0.2915 # 12am-11am
    import_price[14:16,:] = 0.2915 #2pm-4pm
    import_price[23] = 0.2915 #11pm - 12am
    # Set peak prices
    import_price[16:23] = 0.3960

    ret = customer.CustomerModel(
                        export_price,
                        import_price,
                        price_vpp_use=1.0, # pay $1/kWh of grid support
                        day_charge=1.2650,
                        bonus_signup=0, # No welcome credit
    # No minimum soc, however hardware ususally sets it to 0.2
                        soc_min=0.0,
                        soc_min_flag=True, # Can change soc min.
                        label="Globird ZEROHERO"
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
