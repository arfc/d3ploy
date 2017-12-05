import numpy as np
import scipy as sp
import random
import copy

from cyclus.agents import Institution, Agent
from cyclus import lib
import cyclus.typesystem as ts

import statsmodels.api as sm


class NOInst(Institution):
    """
    This institution deploys facilities based on demand curves using 
    Non Optimizing (NO) methods. 
    """

    prototypes=ts.VectorString(
        doc="A list of prototypes that the institution will draw upon to fit" +
              "the demand curve",
        tooltip="List of prototypes the institution can use to meet demand",
        uilabel="Prototypes",
        uitype="oneOrMore"    
    )

    growth_rate=ts.Double(
        doc="This value represents the growth rate that the institution is " +
            "attempting to meet.",
        tooltip="Growth rate of growth commodity",
        uilabel="Growth Rate"    
    )
    
    supply_commod=ts.String(
        doc="The commodity this institution will be monitoring for demand growth. " +
            "The default value of this field is electric power.",
        tooltip="Growth commodity",
        uilabel="Growth Commodity"
    )
    
    demand_commod=ts.String(
        doc="The commodity this institution will be monitoring for demand growth. " +
              "The default value of this field is electric power.",
        tooltip="Growth commodity",
        uilabel="Growth Commodity"
    )

    initial_demand=ts.Double(
        doc="The initial power of the facility",
        tooltip="Initital demand",
        uilabel="Initial demand"
    )

    calc_method=ts.String(
        doc="This is the calculated method used to determine the supply and demand " +
              "for the commodities of this institution. Currently this can be ma for " +
              "moving average, or arma for autoregressive moving average.",
        tooltip="Calculation method used to predict supply/demand",
        uilabel="Calculation Method"
    )
    
    deployed=ts.Int(
        doc="The number of facilities initially deployed to this institution. "+ 
              "This should match the initial facilities in the initial facilities list",
        tooltip="Initial facilities of this institution",
        uilabel="Initial Facilities"
    )

    record=ts.Bool(
        doc="Indicates whether or not the institution should record it's output to text " +
              "file outputs. The output files match the name of the demand commodity of the " +
              "institution.",
        tooltip="Boolean to indicate whether or not to record output to text file.",
        uilabel="Record to Text",
        default=False
    )


    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.commodity_supply = {}
        self.commodity_demand = {}
        self.fac_supply = {}

    
    def enter_notify(self):
        super().enter_notify()
        lib.TIME_SERIES_LISTENERS[self.supply_commod].append(self.extract_supply)
        lib.TIME_SERIES_LISTENERS[self.demand_commod].append(self.extract_demand)         


    def tock(self):
        """
        This is the tock method for the institution. Here the institution determines the difference
        in supply and demand and makes the the decision to deploy facilities or not.     
        """
        time = self.context.time
        diff, supply, demand = self.calc_diff(time)
        if  diff < 0:
            proto = random.choice(self.prototypes)
            #proto_v = self.fac_supply[proto]
            prod_rate = self.commodity_supply[time] / self.deployed
            number = np.ceil(-1*diff/prod_rate)
            self.deployed += number
            i = 0
            while i < number:
                self.context.schedule_build(self, proto)
                i+=1
        if self.record:
            f = open(self.demand_commod+".txt", 'a')
            f.write("Time " + str(time) + " Deployed " + str(self.deployed) + " supply " + str(self.commodity_supply[time]) + " demand " +str(self.commodity_demand[time]) + "\n")   
            f.close()  

    def calc_diff(self, time):
        """
        This function calculates the different in supply and demand for a given facility
        Parameters
        ----------        
        time : int
            This is the time step that the difference is being calculated for.
        Returns
        -------
        diff : double
            This is the difference between supply and demand at [time]
        supply : double
            The calculated supply of the supply commodity at [time].
        demand : double
            The calculated demand of the demand commodity at [time]
        """
        try:
            supply = self.calc_methods[self.calc_method](self, self.commodity_supply)
        except:
            supply = self.calc_methods['ma'](self, self.commodity_supply)
        if not self.commodity_demand:
            self.commodity_demand[time] = self.initial_demand
        if self.demand_commod == 'power':
            demand = self.demand_calc(time+1)
            self.commodity_demand[time] = demand
        else:
            try:
                demand = self.calc_methods[self.calc_method](self, self.commodity_demand)
            except:
                demand = self.calc_methods['ma'](self, self.commodity_demand)
        diff = supply - demand
        return diff, supply, demand

    def extract_supply(self, agent, time, value):
        """
        Gather information on the available supply of a commodity over the
        lifetime of the simulation. 

        Parameters
        ----------
        agent : cyclus agent
            This is the agent that is making the call to the listener.
        time : int
            Timestep that the call is made.
        value : object
            This is the value of the object being recorded in the time
            series.
        """
        if time in self.commodity_supply:
            self.commodity_supply[time] += value
        else:
            self.commodity_supply[time] = value

    
    def extract_demand(self, agent, time, value):
        """
        Gather information on the demand of a commodity over the
        lifetime of the simulation.
        
        Parameters
        ----------
        agent : cyclus agent
            This is the agent that is making the call to the listener.
        time : int
            Timestep that the call is made.
        value : object
            This is the value of the object being recorded in the time
            series.
        """        
        if time in self.commodity_demand:
            self.commodity_demand[time] += value
        else:
            self.commodity_demand[time] = value

    
    def demand_calc(self, time):
        """
        Calculate the electrical demand at a given timestep (time). 
        
        Parameters
        ----------
        time : int
            The timestep that the demand will be calculated at. 
        Returns
        -------
        demand : The calculated demand at a given timestep.
        """
        timestep = self.context.dt
        time = time * timestep
        demand = self.initial_demand * ((1.0+self.growth_rate)**(time/3.154e+7))
        return demand


    def moving_avg_sup(self, ts, order=1):
        """
        Calculates the moving average of a previous [order] entries in
        timeseries [ts]. It will automatically reduce the order if the
        length of ts is shorter than the order. 

        Parameters:
        -----------
        ts : Array of doubles
            An array of time series data to be used for the arma prediction
        order : int
            The number of values used for the moving average. 
        Returns
        -------
        x : The moving average calculated by the function.         
        """
        supply = np.array(list(ts.values()))
        if order >= len(supply):
            order = len(supply) * -1
        else:
            order *= -1
        x = np.average(supply[order:])
        return x

    def predict_arma(self, ts, time=1):
        """
        Predict the value of supply or demand at a given time step using the 
        currently available time series data. This method impliments an ARMA
        calculation to perform the prediciton. 

        Parameters:
        -----------
        ts : Array of doubles
            An array of time series data to be used for the arma prediction
        time: int
            The number of timesteps to predict forward. 
        Returns:
        --------
        x : Predicted value for the time series at chosen timestep (time). 
        """
        v = list(ts.values())
        x = sm.tsa.ARMA(v, (2,0)).fit(disp=-1).forecast(time)[0][time-1]
        return x

    
    def predict_arch(ts, time):
        """
        Predict the value of supply or demand at a given time step using the 
        currently available time series data. This method impliments an ARCH
        calculation to perform the prediciton. 
        """

    """This dictionary is used to select the calculation method used in the 
    institution. 
    """
    calc_methods = {
        'ma' : moving_avg_sup,
        'arma' : predict_arma
    }
