#VPP_model_customer
#To use: import VPP_model_customer as customer
"""
TODO: Code overview
"""

# Imports
import numpy as np
import pandas as pd
from matplotlib import pyplot as plt

class CustomerModelAmber:

    def __init__(
                    self,
                    label=None
    ):
        self.label="no_name"
        if label != None:
            self.label = label

    def __str__(self):
        print("Type: CustomerModelAmber, Name: {}".format(self.label))
