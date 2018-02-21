"""

"""

import random
import copy
import math
from collections import defaultdict
import numpy as np
import scipy as sp

from cyclus.agents import Institution, Agent
from cyclus import lib
import cyclus.typesystem as ts

import statsmodels.api as sm
from arch import arch_model

CALC_METHODS = {}

class NOInst(Institution):
    """
    This institution deploys facilities based on demand curves using 
    Non Optimizing (NO) methods. 
    """

    prototypes = ts.VectorString(
        doc="A list of prototypes that the institution will draw upon to fit" +
              "the demand curve",
        tooltip="List of prototypes the institution can use to meet demand",
        uilabel="Prototypes",
        uitype="oneOrMore"    
    )

    growth_rate = ts.Double(
        doc="This value represents the growth rate that the institution is " +
            "attempting to meet.",
        tooltip="Growth rate of growth commodity",
        uilabel="Growth Rate",
        default="0.02"    
    )
    
    supply_commod = ts.String(
        doc="The commodity this institution will be monitoring for supply growth.",
        tooltip="Supply commodity",
        uilabel="Supply Commodity"
    )
    
    demand_commod = ts.String(
        doc="The commodity this institution will be monitoring for demand growth.",
        tooltip="Growth commodity",
        uilabel="Growth Commodity"
    )

    initial_demand = ts.Double(
        doc="The initial power of the facility",
        tooltip="Initital demand",
        uilabel="Initial demand"
    )

    calc_method = ts.String(
        doc="This is the calculated method used to determine the supply and demand " +
              "for the commodities of this institution. Currently this can be ma for " +
              "moving average, or arma for autoregressive moving average.",
        tooltip="Calculation method used to predict supply/demand",
        uilabel="Calculation Method"
    )
    
    record = ts.Bool(
        doc="Indicates whether or not the institution should record it's output to text " +
              "file outputs. The output files match the name of the demand commodity of the " +
              "institution.",
        tooltip="Boolean to indicate whether or not to record output to text file.",
        uilabel="Record to Text",
        default=False
    )

    supply_std_dev = ts.Double(
        doc="The number of standard deviations off mean for ARMA predictions",
        tooltip="Std Dev off mean for ARMA",
        uilabel="Supple Std Dev",
        default=0.
    )

    demand_std_dev = ts.Double(
        doc="The number of standard deviations off mean for ARMA predictions",
        tooltip="Std Dev off mean for ARMA",
        uilabel="Demand Std Dev",
        default=0.
    )

    steps = ts.Int(
        doc="The number of timesteps forward for ARMA or order of the MA",
        tooltip="Std Dev off mean for ARMA",
        uilabel="Demand Std Dev",
        default=1
    )
    back_steps = ts.Int(
        doc="This is the number of steps backwards from the current time step" +
            "that will be used to make the prediction. If this is set to '0'" +
            "then the calculation will use all values in the time series.",
        tooltip="",
        uilabel="",
        default=10
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.commodity_supply = defaultdict(float)
        self.commodity_demand = defaultdict(float)
        self.fac_supply = {}
        CALC_METHODS['ma'] = self.moving_avg
        CALC_METHODS['arma'] = self.predict_arma
        CALC_METHODS['arch'] = self.predict_arch

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
            ## This is still not correct. If no facilities are present at the start of the
            ## simulation prod_rate will still return zero. More complex fix is required.
            if self.fac_supply[proto]:
                prod_rate = self.fac_supply[proto]
            else:
                print("No facility production rate available for " + proto)                
            number = np.ceil(-1*diff/prod_rate)
            i = 0
            while i < number:
                self.context.schedule_build(self, proto)
                i += 1
        if self.record:
            with open(self.demand_commod+".txt", 'a') as f:
                f.write("Time " + str(time) + " Deployed " + str(len(self.children)) + 
                                              " supply " + str(self.commodity_supply[time]) + 
                                              " demand " +str(self.commodity_demand[time]) + "\n")    

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
            supply = CALC_METHODS[self.calc_method](self.commodity_supply, steps = self.steps, 
                                                    std_dev = self.supply_std_dev,
                                                    back_steps=self.back_steps)
        except (ValueError, np.linalg.linalg.LinAlgError):
            supply = CALC_METHODS['ma'](self.commodity_supply)
        if not self.commodity_demand:
            self.commodity_demand[time] = self.initial_demand
        if self.demand_commod == 'power':
            demand = self.demand_calc(time+1)
            self.commodity_demand[time] = demand
        try:
            demand = CALC_METHODS[self.calc_method](self.commodity_demand, steps = self.steps, 
                                                    std_dev = self.demand_std_dev,
                                                    back_steps=self.back_steps)
        except (np.linalg.linalg.LinAlgError, ValueError):
            demand = CALC_METHODS['ma'](self.commodity_demand)
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
        self.commodity_supply[time] += value
        self.fac_supply[agent.prototype] = value

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
        self.commodity_demand[time] += value

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


    def moving_avg(self, ts, steps=1, std_dev = 0, back_steps=5):
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
        if steps >= len(supply):
            steps = len(supply) * -1
        else:
            steps *= -1
        x = np.average(supply[steps:])
        return x

    def predict_arma(self, ts, steps=1, std_dev = 0, back_steps=5):
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
        v = v[-1*back_steps:]        
        fit = sm.tsa.ARMA(v, (1,0)).fit(disp=-1)
        forecast = fit.forecast(steps)
        x = forecast[0][steps-1] + forecast[1][steps-1]*std_dev
        return x

    
    def predict_arch(self, ts, steps=1, std_dev = 0, back_steps=10):
        """
        Predict the value of supply or demand at a given time step using the 
        currently available time series data. This method impliments an ARCH
        calculation to perform the prediciton. 
        """
        v = list(ts.values())
        model = arch_model(v)
        fit = model.fit(disp='nothing', update_freq=0, show_warning=False)
        forecast = fit.forecast(horizon=steps)
        step = 'h.' + str(steps)
        x = forecast.mean.get(step)[len(v)-steps]
        sd = math.sqrt(forecast.variance.get(step)[len(v)-steps]) * std_dev
        return x+sd

