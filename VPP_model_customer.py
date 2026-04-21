#VPP_model_customer
#To use: import VPP_model_customer as customer
"""
TODO: Code overview
"""

# Imports
import numpy as np
import pandas as pd
from matplotlib import pyplot as plt

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
                month_charge=0.0,
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
        self.price_vpp_use = price_vpp_use
        self.chargeDay = day_charge
        self.chargeMonth = month_charge
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
