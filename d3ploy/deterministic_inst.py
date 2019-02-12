"""
This cyclus archetype uses time series methods to predict the demand and supply
for future time steps and manages the deployment of facilities to ensure
supply is greater than demand. Time series predicition methods can be used
in this archetype.
"""

import math
from collections import defaultdict
import numpy as np
import scipy as sp

from cyclus.agents import Institution, Agent
from cyclus import lib
import cyclus.typesystem as ts

class DeterministicInst(Institution):
    """
    This institution deploys facilities based on demand curves using
    time series methods.
    """

    demand_eq = ts.String(
        doc="This is the string for the demand equation of the driving commodity. " +
        "The equation should use `t' as the dependent variable",
        tooltip="Demand equation for driving commodity",
        uilabel="Demand Equation"
    )

    prototypes = ts.VectorString(
        doc="A list of the prototypes controlled by the institution.",
        tooltip="List of prototypes in the institution.",
        uilabel="Prototypes",
        uitype="oneOrMore"
    )

    fac_rates = ts.VectorString(
        doc="This is the string for the demand equation of the driving commodity. " +
        "The equation should use `t' as the dependent variable",
        tooltip="Demand equation for driving commodity",
        uitype="oneOrMore",
        uilabel="Demand Equation"
    )


    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.commods = {}
        self.construct = []
        self.demand = [0]
        
    def enter_notify(self):
        super().enter_notify() 
        for proto in self.prototypes:
            self.construct.append(0)

    def decision(self):
        self.commods, matrix = self.construct_matrix()
        t = self.context.time
        self.demand.append(self.demand_calc(t+1))
        demand = self.demand[-1] - self.demand[-2]
        results = [0]*len(self.prototypes)
        results[0] = demand
        solve = []
        for proto in self.prototypes:
            solve.append(matrix[proto])
        out = np.linalg.solve(solve, results)
        print(out)
        print(self.construct)
        for i in range(len(out)):
            self.construct[i] += out[i]
        print(self.construct)
        for i in range(len(self.construct)):
            j = 0
            while j < self.construct[i]:
                self.context.schedule_build(self, self.prototypes[i])
                self.construct[i] -= 1
                j+=1       

    def construct_matrix(self):
        matrix = {}
        commodities = {}
        for i in range(len(self.prototypes)):
            proto = self.prototypes[i]
            matrix[proto] = np.array(self.fac_rates[i].split(",")).astype(float)
        return commodities, matrix
    '''    
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
        # self.commodity_dict[commod] = {agent.prototype: value}

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
    '''
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
