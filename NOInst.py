import numpy as np
import scipy as sp
import random

from cyclus.agents import Institution
from cyclus import lib
import cyclus.typesystem as ts


class NOInst(Institution):
"""
This institution deploys facilities based on demand curves using 
Non Optimizing (NO) methods. 
"""

    prototypes = ts.VectorString(
        doc = "A list of prototypes that the institution will draw upon to fit" +
              "the demand curve"
        tooltip = "List of prototypes the institution can use to meet demand"
        uilabel = "Prototypes"
        uitype = "oneOrMore"    
    )

    growth_rate = ts.Double(
        doc = "This value represents the growth rate that the institution is " +
              "attempting to meet."
        tooltip = "Growth rate of growth commodity"
        uilabel = "Growth Rate"    
    )
    
    growth_commod = ts.String(
        doc = "The commodity this institution will be monitoring for demand growth. " +
              "The default value of this field is electric power." 
        tooltip = "Growth commodity"
        uilabel = "Growth Commodity"
        default = "electricity"
    )

    starting_power = ts.Double(
        doc = "The power that this institution will attempt to maintain" 
        tooltip = "Growth commodity"
        uilabel = "Growth Commodity"
        default = "electricity"
    )


    def Build():
    """

    """

    
    def extract_supply(commodity, time):
    """
    Gather information on the available supply of a commodity over the
    lifetime of the simulation. 
    """

    
    def extract_demand(commodity, time):
    """
    Gather information on the demand of a commodity over the
    lifetime of the simulation.

    """

    
    def electric_demand(time):
    """
    Calculate the electrical demand at a given timestep (time). 
    """


    def predict_arma(ts, time, ar_q, ma_p, c=0., ar_w=None, ma_w=None):
    """
    Predict the value of supply or demand at a given time step using the 
    currently available time series data. This method impliments an ARMA
    calculation to perform the prediciton. 

    Parameters:
    -----------
    ts : Array of doubles
        An array of time series data to be used for the arma prediction
    time: int
        The time which is used to determine the predicted value. 

    Returns:
    --------
    X : Predicted value for the time series at chosen timestep (time). 
    """
    x = c
    ma = 0
    for i in range(len(ma_w)):
        ma += w[-1*(i+1)]*ts[-1*(i+1)]
    

    
    def predict_arch(ts, time):
    """
    Predict the value of supply or demand at a given time step using the 
    currently available time series data. This method impliments an ARCH
    calculation to perform the prediciton. 
    """
        
                        
