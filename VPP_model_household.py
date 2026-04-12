#VPP_model_household
#To use: import VPP_model_household as household
"""
TODO: Code overview
"""

# Imports
import numpy as np
import pandas as pd
from matplotlib import pyplot as plt

# Classes
class Household:
    """
    Organise data of one household to be easily accessible
    Try keep this structured so the VPP rules can be applied easily
    """

    def __init__(
                self,
                pv_cap,
                df_demand,
                df_pv,
                label=None
    ):
        self.pvCap = pv_cap
        self.dataDemand = df_demand
        self.dataPV = df_pv
        if label != None:
            self.label = label
        else:
            self.label = "no_name"

    def __str__(self):
        return "Type: Household, name: {}".format(self.label)

    # Other functions
#TODO: Import household data: Store as two dataframes

# Grab entire excel file and convert to pandas dataframe
# Split into pandas dataframe for demand and pv

# Clean the data: detect any weird metering issues or households

# Grab entire AEMO spot pricing info and convert to dataframe

