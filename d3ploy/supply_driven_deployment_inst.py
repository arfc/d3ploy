"""
This cyclus archetype uses time series methods to predict
the supply and capacity for future time steps and manages
the deployment of facilities to ensure capacity is greater
than supply. Time series predicition methods can be used
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
import d3ploy.DO_solvers as do
import d3ploy.ML_solvers as ml
import d3ploy.deployment_inst as di

CALC_METHODS = {}


class SupplyDrivenDeploymentInst(Institution):
    """
    This institution deploys facilities based on demand curves using
    time series methods.
    """

    facility_commod = ts.MapStringString(
        doc="A map of facilities and each of their corresponding" +
        " output commodities",
        tooltip="Map of facilities and output commodities in the " +
        "institution",
        alias=['facility_commod', 'facility', 'commod'],
        uilabel="Facility and Commodities"
    )

    facility_capacity = ts.MapStringDouble(
        doc="A map of facilities and each of their corresponding" +
        " capacities",
        tooltip="Map of facilities and capacities in the " +
        "institution",
        alias=['facility_capacity', 'facility', 'capacity'],
        uilabel="Facility and Capacities"
    )

    facility_pref = ts.MapStringString(
        doc="A map of facilities and each of their corresponding" +
        " preferences",
        tooltip="Map of facilities and preferences in the " +
        "institution",
        alias=['facility_pref', 'facility', 'pref'],
        uilabel="Facility and Preferences",
        default={}
    )

    facility_constraintcommod = ts.MapStringString(
        doc="A map of facilities and each of their corresponding" +
        " constraint commodity",
        tooltip="Map of facilities and constraint commodities in the " +
        "institution",
        alias=['facility_constraintcommod', 'facility', 'constraintcommod'],
        uilabel="Facility and Constraint Commodities",
        default={}
    )

    facility_constraintval = ts.MapStringDouble(
        doc="A map of facilities and each of their corresponding" +
        " constraint values",
        tooltip="Map of facilities and constraint values in the " +
        "institution",
        alias=['facility_constraintval', 'facility', 'constraintval'],
        uilabel="Facility and Constraint Commodity Values",
        default={}
    )

    calc_method = ts.String(
        doc="This is the calculated method used to determine " +
        "the supply and capacity for the commodities of " +
        "this institution. Currently this can be ma for " +
        "moving average, or arma for autoregressive " +
        "moving average.",
        tooltip="Calculation method used to predict supply/capacity",
        uilabel="Calculation Method"
    )

    record = ts.Bool(
        doc="Indicates whether or not the institution " +
        "should record it's output to text file outputs." +
        "The output files match the name of the " +
        "demand commodity of the institution.",
        tooltip="Boolean to indicate whether or not to record output to text file.",
        uilabel="Record to Text",
        default=False)

    steps = ts.Int(
        doc="The number of timesteps forward to predict supply and capacity",
        tooltip="The number of predicted steps forward",
        uilabel="Timesteps for Prediction",
        default=1
    )

    back_steps = ts.Int(
        doc="This is the number of steps backwards " +
            "from the current time step that will " +
            "be used to make the prediction. If " +
            "this is set to '0' then the calculation " +
            "will use all values in the time series.",
        tooltip="",
        uilabel="Back Steps",
        default=10
    )

    capacity_std_dev = ts.Double(
        doc="The standard deviation adjustment for the capacity side.",
        tooltip="The standard deviation adjustment for the capacity side.",
        uilabel="capacity Std Dev",
        default=0
    )

    capacity_buffer = ts.MapStringString(
        doc="The percent above supply the capacity should hit. In decimal" +
            "form",
        tooltip="Buffer Amount in decimal form.",
        alias=['capacity_buffer', 'commod', 'buffer'],
        uilabel="Capacity Buffer",
        default={}
    )

    degree = ts.Int(
        doc="The degree of the fitting polynomial.",
        tooltip="The degree of the fitting polynomial, if using calc methods" +
                " poly, fft, holtz-winter and exponential smoothing." +
                " Additionally, degree is used to as the 'period' input to " +
                "the stepwise_seasonal method.",
        uilabel="Degree Polynomial Fit / Period for stepwise_seasonal",
        default=1
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.commodity_capacity = {}
        self.commodity_supply = {}
        self.rev_commodity_capacity = {}
        self.rev_commodity_supply = {}
        self.fresh = True
        CALC_METHODS['ma'] = no.predict_ma
        CALC_METHODS['arma'] = no.predict_arma
        CALC_METHODS['arch'] = no.predict_arch
        CALC_METHODS['poly'] = do.polyfit_regression
        CALC_METHODS['exp_smoothing'] = do.exp_smoothing
        CALC_METHODS['holt_winters'] = do.holt_winters
        CALC_METHODS['fft'] = do.fft
        CALC_METHODS['sw_seasonal'] = ml.stepwise_seasonal

    def print_variables(self):
        print('commodities: %s' % self.commodity_dict)
        print('calc_method: %s' % self.calc_method)
        print('record: %s' % str(self.record))
        print('steps: %i' % self.steps)
        print('back_steps: %i' % self.back_steps)
        print('capacity_std_dev: %f' % self.capacity_std_dev)

    def enter_notify(self):
        super().enter_notify()
        if self.fresh:
            # convert list of strings to dictionary
            self.commodity_dict = di.build_dict(
                self.facility_commod,
                self.facility_capacity,
                self.facility_pref,
                self.facility_constraintcommod,
                self.facility_constraintval)
            commod_list = list(self.commodity_dict.keys())
            self.buffer_dict = di.build_buffer_dict(self.capacity_buffer,
                                                    commod_list)
            for commod in self.commodity_dict:
                # swap supply and demand for supply_inst
                # change demand into capacity
                lib.TIME_SERIES_LISTENERS["supply" +
                                          commod].append(self.extract_supply)
                lib.TIME_SERIES_LISTENERS["demand" +
                                          commod].append(self.extract_capacity)
                self.commodity_capacity[commod] = defaultdict(float)
                self.commodity_supply[commod] = defaultdict(float)
            self.fresh = False

    def decision(self):
        """
        This is the tock method for decision the institution. Here the institution determines the difference
        in supply and capacity and makes the the decision to deploy facilities or not.
        """
        time = self.context.time
        for commod, proto_dict in self.commodity_dict.items():

            diff, capacity, supply = self.calc_diff(commod, time)
            lib.record_time_series('calc_supply' + commod, self, supply)
            lib.record_time_series('calc_capacity' + commod, self, capacity)

            if diff < 0:
                deploy_dict = solver.deploy_solver(
                    self.commodity_supply, self.commodity_dict, commod, diff, time)
                for proto, num in deploy_dict.items():
                    for i in range(num):
                        self.context.schedule_build(self, proto)
            if self.record:
                out_text = "Time " + str(time) + \
                    " Deployed " + str(len(self.children))
                out_text += " capacity " + \
                    str(self.commodity_capacity[commod][time])
                out_text += " supply " + \
                    str(self.commodity_supply[commod][time]) + "\n"
                with open(commod + ".txt", 'a') as f:
                    f.write(out_text)

    def calc_diff(self, commod, time):
        """
        This function calculates the different in capacity and supply for a given facility
        Parameters
        ----------
        time : int
            This is the time step that the difference is being calculated for.
        Returns
        -------
        diff : double
            This is the difference between capacity and supply at [time]
        capacity : double
            The calculated capacity of the capacity commodity at [time].
        supply : double
            The calculated supply of the supply commodity at [time]
        """
        if time not in self.commodity_supply[commod]:
            t = 0
            self.commodity_supply[commod][time] = 0
        if time not in self.commodity_capacity[commod]:
            self.commodity_capacity[commod][time] = 0.0
        capacity = self.predict_capacity(commod)
        
        if self.buffer_dict[commod][0] == 'p':  
            supply = self.predict_supply(
                commod, time) * (1 + self.buffer_dict[commod][1])
        elif self.buffer_dict[commod][0] == 'n': 
             supply = self.predict_supply(
                commod, time) + self.buffer_dict[commod][1]
        else: 
            raise Exception('You can only choose p (%) or n (double) for buffer size')
        diff = capacity - supply
        return diff, capacity, supply

    def predict_capacity(self, commod):
        if self.calc_method in ['arma', 'ma', 'arch']:
            capacity = CALC_METHODS[self.calc_method](self.commodity_capacity[commod],
                                                      steps=self.steps,
                                                      std_dev=self.capacity_std_dev,
                                                      back_steps=self.back_steps)
        elif self.calc_method in ['poly', 'exp_smoothing', 'holt_winters', 'fft']:
            capacity = CALC_METHODS[self.calc_method](self.commodity_capacity[commod],
                                                      back_steps=self.back_steps,
                                                      degree=self.degree)
        elif self.calc_method in ['sw_seasonal']:
            capacity = CALC_METHODS[self.calc_method](
                self.commodity_capacity[commod], period=self.degree)
        else:
            raise ValueError(
                'The input calc_method is not valid. Check again.')
        return capacity

    def predict_supply(self, commod, time):
        if self.calc_method in ['arma', 'ma', 'arch']:
            supply = CALC_METHODS[self.calc_method](self.commodity_supply[commod],
                                                    steps=self.steps,
                                                    std_dev=self.capacity_std_dev,
                                                    back_steps=self.back_steps)
        elif self.calc_method in ['poly', 'exp_smoothing', 'holt_winters', 'fft']:
            supply = CALC_METHODS[self.calc_method](self.commodity_supply[commod],
                                                    back_steps=self.back_steps,
                                                    degree=self.degree)
        elif self.calc_method in ['sw_seasonal']:
            supply = CALC_METHODS[self.calc_method](
                self.commodity_supply[commod], period=self.degree)
        else:
            raise ValueError(
                'The input calc_method is not valid. Check again.')
        return supply

    def extract_capacity(self, agent, time, value, commod):
        """
        Gather information on the available capacity of a commodity over the
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
        self.commodity_capacity[commod][time] += value
        # update commodities
        # self.commodity_dict[commod] = {agent.prototype: value}

    def extract_supply(self, agent, time, value, commod):
        """
        Gather information on the capacity of a commodity over the
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
