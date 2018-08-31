"""
The Non-Optimizing institution uses ARMA and ARCH to determine the
supply and demand of a commodity. It uses this information to determine
the deployment of the supply side agent. Information use to determine the
deployment is taken from the t-1 time step. This information predicts supply
and demand of the t+1 time step and the process is done on the t time step.
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

    commodities = ts.VectorString(
        doc="A list of commodities that the institution will manage.",
        tooltip="List of commodities in the institution.",
        uilabel="Commodities",
        uitype="oneOrMore"
    )

    reverse_commodities = ts.VectorString(
        doc="A list of commodities that the institution will manage.",
        tooltip="List of commodities in the institution.",
        uilabel="Reversed Commodities",
        uitype="oneOrMore",
        default=[]
    )

    demand_eq = ts.String(
        doc="This is the string for the demand equation of the driving commodity. " +
              "The equation should use `t' as the dependent variable",
        tooltip="Demand equation for driving commodity",
        uilabel="Demand Equation")

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

    steps = ts.Int(
        doc="The number of timesteps forward for ARMA or order of the MA",
        tooltip="The number of predicted steps forward",
        uilabel="Timesteps for Prediction",
        default=2
    )

    back_steps = ts.Int(
        doc="This is the number of steps backwards from the current time step" +
            "that will be used to make the prediction. If this is set to '0'" +
            "then the calculation will use all values in the time series.",
        tooltip="",
        uilabel="Back Steps",
        default=10
    )

    supply_std_dev = ts.Double(
        doc="The standard deviation adjustment for the supple side.",
        tooltip="The standard deviation adjustment for the supple side.",
        uilabel="Supply Std Dev",
        default=0
    )

    demand_std_dev = ts.Double(
        doc="The standard deviation adjustment for the demand side.",
        tooltip="The standard deviation adjustment for the demand side.",
        uilabel="Demand Std Dev",
        default=0
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.commod_to_fac = {}
        self.commodity_supply = {}
        self.commodity_demand = {}
        self.rev_commod_to_fac = {}
        self.rev_commodity_supply = {}
        self.rev_commodity_demand = {}
        self.fac_supply = {}
        self.fresh = True
        CALC_METHODS['ma'] = self.moving_avg
        CALC_METHODS['arma'] = self.predict_arma
        CALC_METHODS['arch'] = self.predict_arch
        print('init')

    def enter_notify(self):
        super().enter_notify()
        if self.fresh:
            print(self.commodities)
            for commod in self.commodities:
                print(commod)
                lib.TIME_SERIES_LISTENERS["supply"+commod].append(self.extract_supply)
                lib.TIME_SERIES_LISTENERS["demand"+commod].append(self.extract_demand)
                print(lib.TIME_SERIES_LISTENERS)
                print(type(lib.TIME_SERIES_LISTENERS["supply"+commod]))
                self.commodity_supply[commod] = defaultdict(float)
                self.commodity_demand[commod] = defaultdict(float)
                self.fac_supply[commod] = {}
                self.commod_to_fac[commod] = []
            self.fresh = False

    def tock(self)
        """
        This is the tock method for the institution. Here the institution determines the difference
        in supply and demand and makes the the decision to deploy facilities or not.
        """
        print('tock')
        time = self.context.time
        for commod, value in self.commod_to_fac.items():
            if len(value)==0:
                continue
            diff, supply, demand = self.calc_diff(commod, time-1)
            print(commod)
            print(self.commod_to_fac)
            if  diff < 0:
                proto = random.choice(self.commod_to_fac[commod])
                ## This is still not correct. If no facilities are present at the start of the
                ## simulation prod_rate will still return zero. More complex fix is required.
                if proto in self.fac_supply[commod]:
                    prod_rate = self.fac_supply[commod][proto]
                else:
                    print("No facility production rate available for " + proto)
                number = np.ceil(-1*diff/prod_rate)
                for i in range(int(number)):
                    self.context.schedule_build(self, proto)
                    i += 1
            if self.record:
                out_text = "Time " + str(time) + " Deployed " + str(len(self.children))
                out_text += " supply " + str(self.commodity_supply[commod][time-1])
                out_text += " demand " + str(self.commodity_demand[commod][time-1]) + "\n"
                with open(commod +".txt", 'a') as f:
                    f.write(out_text)

    def calc_diff(self, commod, time):
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

        if time not in self.commodity_demand[commod]:
            self.commodity_demand[commod][time] = self.initial_demand
        if time not in self.commodity_supply[commod]:
            self.commodity_supply[commod][time] = self.initial_demand
        try:
            supply = CALC_METHODS[self.calc_method](self.commodity_supply[commod],
                                                    steps = self.steps,
                                                    std_dev = self.supply_std_dev,
                                                    back_steps=self.back_steps)
        except (ValueError, np.linalg.linalg.LinAlgError):
            supply = CALC_METHODS['ma'](self.commodity_supply[commod])
        if commod == 'POWER':
            demand = self.demand_calc(time+2)
            self.commodity_demand[commod][time+2] = demand
        try:

            demand = CALC_METHODS[self.calc_method](self.commodity_demand[commod],
                                                    steps = self.steps,
                                                    std_dev = self.demand_std_dev,
                                                    back_steps=self.back_steps)
        except (np.linalg.linalg.LinAlgError, ValueError):
            demand = CALC_METHODS['ma'](self.commodity_demand[commod])
        diff = supply - demand
        return diff, supply, demand

    def extract_supply(self, agent, time, value, commod):
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
        print('EXTRACT SUPPLY')
        commod = commod[6:]
        self.commodity_supply[commod][time] += value
        self.fac_supply[commod][agent.prototype] = value
        print("ASDFADFADSFASSD", agent.prototype, commod)
        if agent.prototype not in self.commod_to_fac[commod]:
            self.commod_to_fac[commod].append(agent.prototype)

    def extract_demand(self, agent, time, value, commod):
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
        commod = commod[6:]
        print("DEMAND", agent.prototype, commod)
        self.commodity_demand[commod][time] += value

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
        t = time * timestep
        demand = eval(self.demand_calc)
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

    def predict_arma(self, ts, steps=2, std_dev = 0, back_steps=5):
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

    def predict_arch(self, ts, steps=2, std_dev = 0, back_steps=10):
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

