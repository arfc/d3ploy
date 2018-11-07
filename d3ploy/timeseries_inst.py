"""
This cyclus archetype uses time series methods to predict the demand and supply
for future time steps and manages the deployment of facilities to ensure
supply is greater than demand. Time series predicition methods can be used
in this archetype. 
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
import d3ploy.solver as solver
import d3ploy.NO_solvers as no

CALC_METHODS = {}

class TimeSeriesInst(Institution):
    """
    This institution deploys facilities based on demand curves using
    time series methods.
    """

    commodities = ts.VectorString(
        doc="A list of commodities that the institution will manage. " +
            "commodity_prototype_capacity format",
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

    driving_commod = ts.String(
        doc="Sets the driving commodity for the institution. That is the " +
            "commodity that no_inst will deploy against the demand equation.",
        tooltip="Driving Commodity",
        uilabel="Driving Commodity",
        default="POWER"
    )

    steps = ts.Int(
        doc="The number of timesteps forward to predict supply and demand",
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
        self.commodity_supply = {}
        self.commodity_demand = {}
        self.rev_commodity_supply = {}
        self.rev_commodity_demand = {}
        self.fresh = True
        CALC_METHODS['ma'] = no.moving_avg
        CALC_METHODS['arma'] = no.predict_arma
        CALC_METHODS['arch'] = no.predict_arch

    def print_variables(self):
        print('commodities: %s' %self.commodity_dict)
        print('demand_eq: %s' %self.demand_eq)
        print('calc_method: %s' %self.calc_method)
        print('record: %s' %str(self.record))
        print('steps: %i' %self.steps)
        print('back_steps: %i' %self.back_steps)
        print('supply_std_dev: %f' %self.supply_std_dev)
        print('demand_std_dev: %f' %self.demand_std_dev)

    def parse_commodities(self, commodities):
        """ This function parses the vector of strings commodity variable
            and replaces the variable as a dictionary. This function should be deleted
            after the map connection is fixed."""
        temp = commodities
        commodity_dict = {}
        for entry in temp:
            z = entry.split('_')
            if z[0] not in commodity_dict.keys():
                commodity_dict[z[0]] = {}
                commodity_dict[z[0]].update({z[1]: float(z[2])})
            else:
                commodity_dict[z[0]].update({z[1]: float(z[2])})
        return commodity_dict

    def enter_notify(self):
        super().enter_notify()
        if self.fresh:
            # convert list of strings to dictionary
            self.commodity_dict = self.parse_commodities(self.commodities)
            for commod in self.commodity_dict:
                lib.TIME_SERIES_LISTENERS["supply"+commod].append(self.extract_supply)
                lib.TIME_SERIES_LISTENERS["demand"+commod].append(self.extract_demand)
                self.commodity_supply[commod] = defaultdict(float)
                self.commodity_demand[commod] = defaultdict(float)
            self.fresh = False


    def decision(self):
        """
        This is the tock method for the institution. Here the institution determines the difference
        in supply and demand and makes the the decision to deploy facilities or not.
        """
        time = self.context.time
        for commod, proto_cap in self.commodity_dict.items():
            if not bool(proto_cap):
                raise ValueError('Prototype and capacity definition for commodity "%s" is missing' %commod)
            diff, supply, demand = self.calc_diff(commod, time)
            lib.record_time_series(commod+'calc_supply', self, supply)
            lib.record_time_series(commod+'calc_demand', self, demand)
            if  diff < 0:
                deploy_dict = solver.deploy_solver(self.commodity_dict, commod, diff)
                for proto, num in deploy_dict.items():
                    for i in range(num):
                        self.context.schedule_build(self, proto)
            if self.record:
                out_text = "Time " + str(time) + " Deployed " + str(len(self.children))
                out_text += " supply " + str(self.commodity_supply[commod][time])
                out_text += " demand " + str(self.commodity_demand[commod][time]) + "\n"
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
            t = 0
            self.commodity_demand[commod][time] = int(eval(self.demand_eq))
        if time not in self.commodity_supply[commod]:
            self.commodity_supply[commod][time] = 0.0
        try:
            supply = CALC_METHODS[self.calc_method](self.commodity_supply[commod],
                                                    steps = self.steps,
                                                    std_dev = self.supply_std_dev,
                                                    back_steps=self.back_steps)
        except (ValueError, np.linalg.linalg.LinAlgError):
            supply = CALC_METHODS['ma'](self.commodity_supply[commod])
        if commod == self.driving_commod:
            demand = self.demand_calc(time+1)
            self.commodity_demand[commod][time+1] = demand
        else:
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
        commod = commod[6:]
        self.commodity_supply[commod][time] += value
        # update commodities
        #self.commodity_dict[commod] = {agent.prototype: value}

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
        t = time
        demand = eval(self.demand_eq)
        return demand
