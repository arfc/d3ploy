"""
This python file that compares calc methods for difference scenarios.

How to use:
python [file name]

A scenario_#_output.txt file is output for each scenario.
In each text file, the chi2 goodness of fit and supply falling below demand results are shown
and the best calc method is determined for each type of results.


"""

import json
import re
import subprocess
import os
import sqlite3 as lite
import copy
import glob
import sys
from matplotlib import pyplot as plt
import numpy as np
import pandas as pd
import d3ploy.tester as tester
import d3ploy.plotter as plotter
import collections


# Delete previously generated files
direc = os.listdir('./')
hit_list = glob.glob('*.sqlite') + glob.glob('*.json') + \
    glob.glob('*.png') + glob.glob('*.csv') + glob.glob('*.txt')
for file in hit_list:
    os.remove(file)

ENV = dict(os.environ)
ENV['PYTHONPATH'] = ".:" + ENV.get('PYTHONPATH', '')


##### List of types of calc methods that are to be tested #####
calc_methods = ["ma", "arma", "arch", "poly",
                "exp_smoothing", "holt_winters", "fft"]

scenario_template = {
    "simulation": {
        "archetypes": {
            "spec": [
                    {"lib": "agents", "name": "NullRegion"},
                    {"lib": "cycamore", "name": "Source"},
                    {"lib": "cycamore", "name": "Reactor"},
                    {"lib": "cycamore", "name": "Sink"},
                    {"lib": "d3ploy.demand_driven_deployment_inst", "name": "DemandDrivenDeploymentInst"}
            ]
        },
        "control": {"duration": "100", "startmonth": "1", "startyear": "2000"},
        "recipe": [
            {
                "basis": "mass",
                "name": "fresh_uox",
                "nuclide": [{"comp": "0.711", "id": "U235"}, {"comp": "99.289", "id": "U238"}]
            },
            {
                "basis": "mass",
                "name": "spent_uox",
                "nuclide": [{"comp": "50", "id": "Kr85"}, {"comp": "50", "id": "Cs137"}]
            }
        ]}}


######################################SCENARIO 1##########################
# scenario 1, source -> sink
scenario_1_input = {}
demand_eq = "1000*t"

for calc_method in calc_methods:
    scenario_1_input[calc_method] = copy.deepcopy(scenario_template)
    scenario_1_input[calc_method]["simulation"].update({"facility": [{
        "config": {"Source": {"outcommod": "fuel",
                              "outrecipe": "fresh_uox",
                              "throughput": "3000"}},
        "name": "source"
    },
        {
        "config": {"Sink": {"in_commods": {"val": "fuel"},
                            "max_inv_size": "1e6"}},
        "name": "sink"
    },
        {
        "config": {
            "Reactor": {
                "assem_size": "1000",
                "cycle_time": "1",
                "fuel_incommods": {"val": "fuel"},
                "fuel_inrecipes": {"val": "fresh_uox"},
                "fuel_outcommods": {"val": "spentfuel"},
                "fuel_outrecipes": {"val": "spent_uox"},
                "n_assem_batch": "1",
                "n_assem_core": "3",
                "power_cap": "1000",
                "refuel_time": "1",
            }
        },
        "name": "reactor"
    }]})
    scenario_1_input[calc_method]["simulation"].update({"region": {
        "config": {"NullRegion": "\n      "},
        "institution": {
            "config": {
                "DemandDrivenDeploymentInst": {
                    "calc_method": calc_method,
                    "facility_commod": {
                        "item": [
                            {"commod": "fuel", "facility": "source"}
                        ]
                    },
                    "facility_capacity": {
                        "item": [
                            {"capacity": "3000", "facility": "source"}
                        ]
                    },
                    "driving_commod": "fuel",
                    "demand_eq": demand_eq,
                    "record": "1",
                    "steps": "1"
                }
            },
            "name": "source_inst"
        },
        "name": "SingleRegion"
    }})

metric_dict = {}

for calc_method in calc_methods:
    name = 'scenario_1_input_' + calc_method
    input_file = name + '.json'
    output_file = name + '.sqlite'
    with open(input_file, 'w') as f:
        json.dump(scenario_1_input[calc_method], f)
    s = subprocess.check_output(['cyclus', '-o', output_file, input_file],
                                universal_newlines=True, env=ENV)

    # Initialize dicts
    all_dict_fuel = {}
    agent_entry_dict = {}

    all_dict_fuel = tester.supply_demand_dict_driving(output_file,
                                                      demand_eq, 'fuel')
    agent_entry_dict['fuel'] = tester.get_agent_dict(output_file, ['source'])
    plotter.plot_demand_supply_agent(
        all_dict_fuel,
        agent_entry_dict['fuel'],
        'fuel',
        name + '_fuel',
        True,
        False,
        False)

    metric_dict = tester.metrics(all_dict_fuel, metric_dict,
                                 calc_method, 'fuel', True)

    df = pd.DataFrame(metric_dict)
    df.to_csv('scenario_1_output.csv')

##########################################################################

######################################SCENARIO 2##########################
# scenario 2, source -> reactor (cycle time = 1, refuel time = 0) -> sink
scenario_2_input = {}
demand_eq = "1000*t"

for calc_method in calc_methods:
    scenario_2_input[calc_method] = copy.deepcopy(scenario_template)
    scenario_2_input[calc_method]["simulation"].update({"facility": [{
        "config": {"Source": {"outcommod": "fuel",
                              "outrecipe": "fresh_uox",
                              "throughput": "3000"}},
        "name": "source"
    },
        {
        "config": {"Sink": {"in_commods": {"val": "spentfuel"},
                            "max_inv_size": "1e6"}},
        "name": "sink"
    },
        {
        "config": {
            "Reactor": {
                "assem_size": "1000",
                "cycle_time": "1",
                "fuel_incommods": {"val": "fuel"},
                "fuel_inrecipes": {"val": "fresh_uox"},
                "fuel_outcommods": {"val": "spentfuel"},
                "fuel_outrecipes": {"val": "spent_uox"},
                "n_assem_batch": "1",
                "n_assem_core": "3",
                "power_cap": "1000",
                "refuel_time": "0",
            }
        },
        "name": "reactor"
    }]})
    scenario_2_input[calc_method]["simulation"].update({"region": {
        "config": {"NullRegion": "\n      "},
        "institution": {
            "config": {
                "DemandDrivenDeploymentInst": {
                    "calc_method": calc_method,
                    "facility_commod": {
                        "item": [
                            {"commod": "fuel", "facility": "source"},
                            {"commod": "POWER", "facility": "reactor"}
                        ]
                    },
                    "facility_capacity": {
                        "item": [
                            {"capacity": "3000", "facility": "source"},
                            {"capacity": "1000", "facility": "reactor"}
                        ]
                    },
                    "driving_commod": "POWER",
                    "demand_eq": demand_eq,
                    "record": "1",
                    "steps": "1"
                }
            },
            "name": "source_inst"
        },
        "name": "SingleRegion"
    }})

metric_dict = {}

for calc_method in calc_methods:
    name = "scenario_2_input_" + calc_method
    input_file = name + ".json"
    output_file = name + ".sqlite"
    with open(input_file, 'w') as f:
        json.dump(scenario_2_input[calc_method], f)

    s = subprocess.check_output(['cyclus', '-o', output_file, input_file],
                                universal_newlines=True, env=ENV)

    # Initialize dicts
    all_dict_power = {}
    all_dict_fuel = {}
    agent_entry_dict = {}

    all_dict_power = tester.supply_demand_dict_driving(
        output_file, demand_eq, 'power')
    all_dict_fuel = tester.supply_demand_dict_nondriving(
        output_file, 'fuel', True)

    agent_entry_dict['power'] = tester.get_agent_dict(output_file, ['reactor'])
    agent_entry_dict['fuel'] = tester.get_agent_dict(output_file, ['source'])
    # plots demand, supply, calculated demand, calculated supply for the
    # scenario for each calc method
    plotter.plot_demand_supply_agent(
        all_dict_power,
        agent_entry_dict['power'],
        'power',
        name + '_power',
        True,
        False,
        False)
    plotter.plot_demand_supply_agent(
        all_dict_fuel,
        agent_entry_dict['fuel'],
        'fuel',
        name + '_fuel',
        True,
        False,
        False)

    metric_dict = tester.metrics(
        all_dict_power,
        metric_dict,
        calc_method,
        'power',
        True)
    metric_dict = tester.metrics(
        all_dict_fuel,
        metric_dict,
        calc_method,
        'fuel',
        True)

    df = pd.DataFrame(metric_dict)
    df.to_csv('scenario_2_output.csv')


######################################SCENARIO 3##########################
# scenario 3, source -> reactor (cycle time = 18, refuel time = 1) -> sink
scenario_3_input = {}
demand_eq = "1000*t"

for calc_method in calc_methods:
    scenario_3_input[calc_method] = copy.deepcopy(scenario_template)
    scenario_3_input[calc_method]["simulation"].update({"facility": [{
        "config": {"Source": {"outcommod": "fuel",
                              "outrecipe": "fresh_uox",
                              "throughput": "3000"}},
        "name": "source"
    },
        {
        "config": {"Sink": {"in_commods": {"val": "spentfuel"},
                            "max_inv_size": "1e6"}},
        "name": "sink"
    },
        {
        "config": {
            "Reactor": {
                "assem_size": "1000",
                "cycle_time": "18",
                "fuel_incommods": {"val": "fuel"},
                "fuel_inrecipes": {"val": "fresh_uox"},
                "fuel_outcommods": {"val": "spentfuel"},
                "fuel_outrecipes": {"val": "spent_uox"},
                "n_assem_batch": "1",
                "n_assem_core": "3",
                "power_cap": "1000",
                "refuel_time": "1",
            }
        },
        "name": "reactor"
    }]})
    scenario_3_input[calc_method]["simulation"].update({"region": {
        "config": {"NullRegion": "\n      "},
        "institution": {
            "config": {
                "DemandDrivenDeploymentInst": {
                    "calc_method": calc_method,
                    "facility_commod": {
                        "item": [
                            {"commod": "fuel", "facility": "source"},
                            {"commod": "POWER", "facility": "reactor"}
                        ]
                    },
                    "facility_capacity": {
                        "item": [
                            {"capacity": "3000", "facility": "source"},
                            {"capacity": "1000", "facility": "reactor"}
                        ]
                    },
                    "driving_commod": "POWER",
                    "demand_eq": demand_eq,
                    "record": "1",
                    "steps": "1"
                }
            },
            "name": "source_inst"
        },
        "name": "SingleRegion"
    }})


metric_dict = {}

for calc_method in calc_methods:
    name = "scenario_3_input_" + calc_method
    input_file = name + ".json"
    output_file = name + ".sqlite"
    with open(input_file, 'w') as f:
        json.dump(scenario_3_input[calc_method], f)
    s = subprocess.check_output(['cyclus', '-o', output_file, input_file],
                                universal_newlines=True, env=ENV)

    # Initialize dicts
    all_dict_power = {}
    all_dict_fuel = {}
    agent_entry_dict = {}

    all_dict_power = tester.supply_demand_dict_driving(
        output_file, demand_eq, 'power')
    all_dict_fuel = tester.supply_demand_dict_nondriving(
        output_file, 'fuel', True)
    agent_entry_dict['power'] = tester.get_agent_dict(output_file, ['reactor'])
    agent_entry_dict['fuel'] = tester.get_agent_dict(output_file, ['source'])

    # plots demand, supply, calculated demand, calculated supply for the
    # scenario for each calc method
    plotter.plot_demand_supply_agent(
        all_dict_power,
        agent_entry_dict['power'],
        'power',
        name + '_power',
        True,
        False,
        False)
    plotter.plot_demand_supply_agent(
        all_dict_fuel,
        agent_entry_dict['fuel'],
        'fuel',
        name + '_fuel',
        True,
        False,
        False)

    metric_dict = tester.metrics(
        all_dict_power,
        metric_dict,
        calc_method,
        'power',
        True)
    metric_dict = tester.metrics(
        all_dict_fuel,
        metric_dict,
        calc_method,
        'fuel',
        True)

    df = pd.DataFrame(metric_dict)
    df.to_csv('scenario_3_output.csv')

######################################SCENARIO 4##########################
# scenario 4, source -> reactor (cycle time = 1, refuel time = 0) -> sink
scenario_4_input = {}
demand_eq = "10*(1+1.5)**(t/12)"

for calc_method in calc_methods:
    scenario_4_input[calc_method] = copy.deepcopy(scenario_template)
    scenario_4_input[calc_method]["simulation"].update({"facility": [{
        "config": {"Source": {"outcommod": "fuel",
                              "outrecipe": "fresh_uox",
                              "throughput": "3000"}},
        "name": "source"
    },
        {
        "config": {"Sink": {"in_commods": {"val": "spentfuel"},
                            "max_inv_size": "1e6"}},
        "name": "sink"
    },
        {
        "config": {
            "Reactor": {
                "assem_size": "1000",
                "cycle_time": "1",
                "fuel_incommods": {"val": "fuel"},
                "fuel_inrecipes": {"val": "fresh_uox"},
                "fuel_outcommods": {"val": "spentfuel"},
                "fuel_outrecipes": {"val": "spent_uox"},
                "n_assem_batch": "1",
                "n_assem_core": "3",
                "power_cap": "1000",
                "refuel_time": "0",
            }
        },
        "name": "reactor"
    }]})
    scenario_4_input[calc_method]["simulation"].update({"region": {
        "config": {"NullRegion": "\n      "},
        "institution": {
            "config": {
                "DemandDrivenDeploymentInst": {
                    "calc_method": calc_method,
                    "facility_commod": {
                        "item": [
                            {"commod": "fuel", "facility": "source"},
                            {"commod": "POWER", "facility": "reactor"}
                        ]
                    },
                    "facility_capacity": {
                        "item": [
                            {"capacity": "3000", "facility": "source"},
                            {"capacity": "1000", "facility": "reactor"}
                        ]
                    },
                    "driving_commod": "POWER",
                    "demand_eq": demand_eq,
                    "record": "1",
                    "steps": "1"
                }
            },
            "name": "source_inst"
        },
        "name": "SingleRegion"
    }})


metric_dict = {}

for calc_method in calc_methods:
    name = "scenario_4_input_" + calc_method
    input_file = name + ".json"
    output_file = name + ".sqlite"
    with open(input_file, 'w') as f:
        json.dump(scenario_4_input[calc_method], f)
    s = subprocess.check_output(['cyclus', '-o', output_file, input_file],
                                universal_newlines=True, env=ENV)

    # Initialize dicts
    all_dict_power = {}
    all_dict_fuel = {}
    agent_entry_dict = {}

    all_dict_power = tester.supply_demand_dict_driving(
        output_file, demand_eq, 'power')
    all_dict_fuel = tester.supply_demand_dict_nondriving(
        output_file, 'fuel', True)

    agent_entry_dict['power'] = tester.get_agent_dict(output_file, ['reactor'])
    agent_entry_dict['fuel'] = tester.get_agent_dict(output_file, ['source'])
    # plots demand, supply, calculated demand, calculated supply for the
    # scenario for each calc method
    plotter.plot_demand_supply_agent(
        all_dict_power,
        agent_entry_dict['power'],
        'power',
        name + '_power',
        True,
        False,
        False)
    plotter.plot_demand_supply_agent(
        all_dict_fuel,
        agent_entry_dict['fuel'],
        'fuel',
        name + '_fuel',
        True,
        False,
        False)

    metric_dict = tester.metrics(
        all_dict_power,
        metric_dict,
        calc_method,
        'power',
        True)
    metric_dict = tester.metrics(
        all_dict_fuel,
        metric_dict,
        calc_method,
        'fuel',
        True)

    df = pd.DataFrame(metric_dict)
    df.to_csv('scenario_4_output.csv')
