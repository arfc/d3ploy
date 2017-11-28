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
              "the demand curve",
        tooltip = "List of prototypes the institution can use to meet demand",
        uilabel = "Prototypes",
        uitype = "oneOrMore"    
    )

    growth_rate = ts.Double(
        doc = "This value represents the growth rate that the institution is " +
              "attempting to meet.",
        tooltip = "Growth rate of growth commodity",
        uilabel = "Growth Rate"    
    )
    
    growth_commod = ts.String(
        doc = "The commodity this institution will be monitoring for demand growth. " +
              "The default value of this field is electric power.",
        tooltip = "Growth commodity",
        uilabel = "Growth Commodity"
    )

    initial_demand = ts.Double(
        doc = "The initial power of the facility",
        tooltip = "Initital demand",
        uilabel = "Initial demand"
    )

    #The supply of a commodity
    commodity_supply = {}
    deployed = 0

    def tick(self):
        if self.growth_commod not in lib.TIME_SERIES_LISTENERS:
            lib.TIME_SERIES_LISTENERS[self.growth_commod].append(self.extract_supply)
        print("Total Facilities deployed: " + str(self.deployed))

    def tock(self):
        """
        #Method for the deployment of facilities.     
        """
        time = self.context.time
        diff = self.demand_calc(time+1) - self.moving_avg_sup(5)
        print("Demand:" +str(self.demand_calc(time+1)) + "  Supply:" +  str(self.moving_avg_sup(5)))
        if  diff > 0:
            proto = random.choice(self.prototypes)
            self.deployed += 1          
            self.context.schedule_build(self, proto)        

    
    def extract_supply(self, agent, time, value):
        """
        Gather information on the available supply of a commodity over the
        lifetime of the simulation. 
        """
        if time in self.commodity_supply:
            self.commodity_supply[time] += value
        else:
            self.commodity_supply[time] = value

    
    def extract_demand(commodity, time):
        """
        Gather information on the demand of a commodity over the
        lifetime of the simulation.
        """

    
    def demand_calc(self, time):
        """
        Calculate the electrical demand at a given timestep (time). 
        Parameters
        ----------
        time : int
            The timestep that the demand will be calculated at. 
        """
        timestep = self.context.dt / 86400 / 28
        demand = self.initial_demand * ((1.0+self.growth_rate)**(time/timestep))
        return demand


    def moving_avg_sup(self, order):
        supply = np.array(list(self.commodity_supply.values()))
        if order >= len(supply):
            order = len(supply) * -1
        else:
            order *= -1
        x = np.average(supply[order:])
        return x    

    def predict_arma(self, ts, epsi, time, ar_w, ma_w, q=1, p=1, c=0.):
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
        i, j, ar, ma = 0
        vals = np.array(list(ts.values()) 
        while i < q:
            ar += epsi[(i+1)*-1]*ar_w[i*-1]
            i++
        while j < p:
            ma += vals[j*-1]*ma_w[j*-1]
            j++       
        x = epsi[-1] + ar + ma + c
        return x

    
    def predict_arch(ts, time):
        """
        Predict the value of supply or demand at a given time step using the 
        currently available time series data. This method impliments an ARCH
        calculation to perform the prediciton. 
        """
