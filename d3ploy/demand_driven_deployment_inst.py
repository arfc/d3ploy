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
import d3ploy.DO_solvers as do
import d3ploy.ML_solvers as ml
import d3ploy.deployment_inst as di

CALC_METHODS = {}


class DemandDrivenDeploymentInst(Institution):
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
        uilabel="Calculation Method")

    record = ts.Bool(
        doc="Indicates whether or not the institution should record it's output to text " +
        "file outputs. The output files match the name of the demand commodity of the " +
        "institution.",
        tooltip="Boolean to indicate whether or not to record output to text file.",
        uilabel="Record to Text",
        default=False)

    driving_commod = ts.String(
        doc="Sets the driving commodity for the institution. That is the " +
            "commodity that no_inst will deploy against the demand equation.",
        tooltip="Driving Commodity",
        uilabel="Driving Commodity",
        default="POWER"
    )

    installed_cap = ts.Bool(
        doc="True if facility deployment is governed by installed capacity. " +
        "False if deployment is governed by actual commodity supply",
        tooltip="Boolean to indicate whether or not to use installed" +
                "capacity as supply",
        uilabel="installed cap",
        default=False)

    steps = ts.Int(
        doc="The number of timesteps forward to predict supply and demand",
        tooltip="The number of predicted steps forward",
        uilabel="Timesteps for Prediction",
        default=1
    )

    back_steps = ts.Int(
        doc="This is the number of steps backwards from the current time step" +
        "that will be used to make the prediction. If this is set to '0'" +
        "then the calculation will use all values in the time series.",
        tooltip="",
        uilabel="Back Steps",
        default=10)

    supply_std_dev = ts.Double(
        doc="The standard deviation adjustment for the supple side.",
        tooltip="The standard deviation adjustment for the supple side.",
        uilabel="Supply Std Dev",
        default=0
    )

    buffer_type = ts.MapStringString(
        doc="Indicates whether the buffer is in percentage or float form, perc: %," +
        "float: float for each commodity",
        tooltip="Supply buffer in Percentage or float form for each commodity",
        alias=[
            'buffer_type',
            'commod',
            'type'],
        uilabel="Supply Buffer type",
        default={})

    supply_buffer = ts.MapStringDouble(
        doc="Supply buffer size: Percentage or float amount ",
        tooltip="Supply buffer Amount.",
        alias=['supply_buffer', 'commod', 'buffer'],
        uilabel="Supply Buffer",
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
        self.commodity_supply = {}
        self.commodity_demand = {}
        self.installed_capacity = {}
        self.fac_commod = {}
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
        print('demand_eq: %s' % self.demand_eq)
        print('calc_method: %s' % self.calc_method)
        print('record: %s' % str(self.record))
        print('steps: %i' % self.steps)
        print('back_steps: %i' % self.back_steps)
        print('supply_std_dev: %f' % self.supply_std_dev)

    def enter_notify(self):
        super().enter_notify()
        if self.fresh:
            # convert input into dictionary
            self.commodity_dict = di.build_dict(
                self.facility_commod,
                self.facility_capacity,
                self.facility_pref,
                self.facility_constraintcommod,
                self.facility_constraintval)
            for commod, proto_dict in self.commodity_dict.items():
                protos = proto_dict.keys()
                for proto in protos:
                    self.fac_commod[proto] = commod
            self.commod_list = list(self.commodity_dict.keys())
            for commod in self.commod_list:
                self.installed_capacity[commod] = defaultdict(float)
                self.installed_capacity[commod][0] = 0.
            for commod, commod_dict in self.commodity_dict.items():
                for proto, proto_dict in commod_dict.items():
                    if proto_dict['constraint_commod'] != '0':
                        self.commod_list.append(
                            proto_dict['constraint_commod'])
            self.buffer_dict = di.build_buffer_dict(self.supply_buffer,
                                                    self.commod_list)
            self.buffer_type_dict = di.build_buffer_type_dict(
                self.buffer_type, self.commod_list)
            for commod in self.commod_list:
                lib.TIME_SERIES_LISTENERS["supply" +
                                          commod].append(self.extract_supply)
                lib.TIME_SERIES_LISTENERS["demand" +
                                          commod].append(self.extract_demand)
                self.commodity_supply[commod] = defaultdict(float)
                self.commodity_demand[commod] = defaultdict(float)
            for child in self.children:
                itscommod = self.fac_commod[child.prototype]
                self.installed_capacity[itscommod][0] += self.commodity_dict[itscommod][child.prototype]['cap']
            self.fresh = False

    def decision(self):
        """
        This is the tock method for decision the institution. Here the institution determines the difference
        in supply and demand and makes the the decision to deploy facilities or not.
        """
        time = self.context.time
        for commod, proto_dict in self.commodity_dict.items():
            diff, supply, demand = self.calc_diff(commod, time)
            lib.record_time_series('calc_supply' + commod, self, supply)
            lib.record_time_series('calc_demand' + commod, self, demand)
            if diff < 0:
                if self.installed_cap:
                    deploy_dict = solver.deploy_solver(
                        self.installed_capacity, self.commodity_dict, commod, diff, time)
                else:
                    deploy_dict = solver.deploy_solver(
                        self.commodity_supply, self.commodity_dict, commod, diff, time)
                for proto, num in deploy_dict.items():
                    for i in range(num):
                        self.context.schedule_build(self, proto)
                # update installed capacity dict
                for proto, num in deploy_dict.items():
                    self.installed_capacity[commod][time + 1] = \
                        self.installed_capacity[commod][time] + \
                        self.commodity_dict[commod][proto]['cap'] * num
            else:
                self.installed_capacity[commod][time +
                                                1] = self.installed_capacity[commod][time]

            if self.record:
                out_text = "Time " + str(time) + \
                    " Deployed " + str(len(self.children))
                out_text += " supply " + \
                    str(self.commodity_supply[commod][time])
                out_text += " demand " + \
                    str(self.commodity_demand[commod][time]) + "\n"
                with open(commod + ".txt", 'a') as f:
                    f.write(out_text)
        for child in self.children:
            if child.exit_time == time:
                itscommod = self.fac_commod[child.prototype]
                self.installed_capacity[itscommod][time +
                                                   1] -= self.commodity_dict[itscommod][child.prototype]['cap']

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
            self.commodity_demand[commod][time] = eval(self.demand_eq)
        if time not in self.commodity_supply[commod]:
            self.commodity_supply[commod][time] = 0.0
        supply = self.predict_supply(commod)

        if self.buffer_type_dict[commod] == 'perc':
            demand = self.predict_demand(
                commod, time) * (1 + self.buffer_dict[commod])
        elif self.buffer_type_dict[commod] == 'float':
            demand = self.predict_demand(
                commod, time) + self.buffer_dict[commod]
        else:
            raise Exception(
                'You can only choose perc (%) or float (double) for buffer size')

        diff = supply - demand
        return diff, supply, demand

    def predict_supply(self, commod):
        def target(incommod):
            if self.installed_cap:
                return self.installed_capacity[incommod]
            else:
                return self.commodity_supply[incommod]
        try:
            if self.calc_method in ['arma', 'ma', 'arch']:
                supply = CALC_METHODS[self.calc_method](target(commod),
                                                        steps=self.steps,
                                                        std_dev=self.supply_std_dev,
                                                        back_steps=self.back_steps)
            elif self.calc_method in ['poly', 'exp_smoothing', 'holt_winters', 'fft']:
                supply = CALC_METHODS[self.calc_method](target(commod),
                                                        back_steps=self.back_steps,
                                                        degree=self.degree)
            elif self.calc_method in ['sw_seasonal']:
                supply = CALC_METHODS[self.calc_method](
                    target(commod), period=self.degree)
            else:
                raise ValueError(
                    'The input calc_method is not valid. Check again.')
        except:
            capacity = CALC_METHODS['ma'](target(commod),
                              steps=1,
                              std_dev=self.capacity_std_dev,
                              back_steps=1)
        return supply

    def predict_demand(self, commod, time):
        if commod == self.driving_commod:
            demand = self.demand_calc(time + 1)
            self.commodity_demand[commod][time + 1] = demand
        else:
            try:
                if self.calc_method in ['arma', 'ma', 'arch']:
                    demand = CALC_METHODS[self.calc_method](self.commodity_demand[commod],
                                                            steps=self.steps,
                                                            std_dev=self.supply_std_dev,
                                                            back_steps=self.back_steps)
                elif self.calc_method in ['poly', 'exp_smoothing', 'holt_winters', 'fft']:
                    demand = CALC_METHODS[self.calc_method](self.commodity_demand[commod],
                                                            back_steps=self.back_steps,
                                                            degree=self.degree)
                elif self.calc_method in ['sw_seasonal']:
                    demand = CALC_METHODS[self.calc_method](
                        self.commodity_demand[commod], period=self.degree)
                else:
                    raise ValueError(
                        'The input calc_method is not valid. Check again.')
            except:
                capacity = CALC_METHODS['ma'](target(commod),
                              steps=1,
                              std_dev=self.capacity_std_dev,
                              back_steps=1)
        return demand

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
