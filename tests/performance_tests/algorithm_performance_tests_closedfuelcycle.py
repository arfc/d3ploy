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

######################################SCENARIO 7##########################
scenario_7_input = {}
demand_eq = "1000*t"

for calc_method in calc_methods:
    scenario_7_input[calc_method] = {
        "simulation": {
            "archetypes": {
                "spec": [
                    {"lib": "agents", "name": "NullRegion"},
                    {"lib": "cycamore", "name": "Source"},
                    {"lib": "cycamore", "name": "Reactor"},
                    {"lib": "cycamore", "name": "Mixer"},
                    {"lib": "cycamore", "name": "Separations"},
                    {"lib": "cycamore", "name": "Storage"},
                    {"lib": "cycamore", "name": "Sink"},
                    {"lib": "d3ploy.demand_driven_deployment_inst", "name": "DemandDrivenDeploymentInst"},
                    {
                        "lib": "d3ploy.supply_driven_deployment_inst",
                        "name": "SupplyDrivenDeploymentInst"
                    }
                ]
            },
            "control": {"duration": "20", "startmonth": "1", "startyear": "2000"},
            "facility": [
                {
                    "config": {
                        "Source": {
                            "outcommod": "sourceoutput",
                            "outrecipe": "source_recipe",
                            "throughput": "3000"
                        }
                    },
                    "name": "source"
                },
                {
                    "config": {
                        "Separations": {
                            "feed_commod_prefs": {"val": "1.0"},
                            "feed_commods": {"val": "reactor1output"},
                            "feed_recipe": "source_recipe",
                            "feedbuf_size": "1e4",
                            "leftover_commod": "reprocess_waste1",
                            "leftoverbuf_size": "1e4",
                            "streams": {
                                "item": [
                                    {
                                        "commod": "separations1Pu",
                                        "info": {"buf_size": "1e4", "efficiencies": {"item": {"comp": "Pu", "eff": "1"}}}
                                    },
                                    {
                                        "commod": "separations1U",
                                        "info": {"buf_size": "1e4", "efficiencies": {"item": {"comp": "U", "eff": "1"}}}
                                    }
                                ]
                            },
                            "throughput": "1e4"
                        }
                    },
                    "name": "separations1"
                },
                {
                    "config": {
                        "Mixer": {
                            "in_streams": {
                                "stream": [
                                    {
                                        "commodities": {
                                            "item": [
                                                {"commodity": "separations1Pu", "pref": "1.0"},
                                                {"commodity": "separations2Pu", "pref": "1.0"}
                                            ]
                                        },
                                        "info": {"buf_size": "1e4", "mixing_ratio": "0.5"}
                                    },
                                    {
                                        "commodities": {
                                            "item": [
                                                {"commodity": "separations1U", "pref": "1.0"},
                                                {"commodity": "separations2U", "pref": "1.0"}
                                            ]
                                        },
                                        "info": {"buf_size": "1e4", "mixing_ratio": "0.5"}
                                    }
                                ]
                            },
                            "out_buf_size": "1e4",
                            "out_commod": "mixeroutput",
                            "throughput": "1e4"
                        }
                    },
                    "name": "mixer"
                },
                {
                    "config": {
                        "Reactor": {
                            "assem_size": "1000",
                            "cycle_time": "1",
                            "fuel_incommods": {"val": "sourceoutput"},
                            "fuel_inrecipes": {"val": "source_recipe"},
                            "fuel_outcommods": {"val": "reactor1output"},
                            "fuel_outrecipes": {"val": "reactor_recipe"},
                            "n_assem_batch": "1",
                            "n_assem_core": "3",
                            "power_cap": "1000",
                            "refuel_time": "0"
                        }
                    },
                    "name": "reactor1"
                },
                {
                    "config": {
                        "Reactor": {
                            "assem_size": "1000",
                            "cycle_time": "1",
                            "fuel_incommods": {"val": "mixeroutput"},
                            "fuel_inrecipes": {"val": "source_recipe"},
                            "fuel_outcommods": {"val": "reactor2output"},
                            "fuel_outrecipes": {"val": "reactor_recipe"},
                            "n_assem_batch": "1",
                            "n_assem_core": "3",
                            "power_cap": "1000",
                            "refuel_time": "0"
                        }
                    },
                    "name": "reactor2"
                },
                {
                    "config": {
                        "Separations": {
                            "feed_commod_prefs": {"val": "1.0"},
                            "feed_commods": {"val": "reactor2output"},
                            "feed_recipe": "source_recipe",
                            "feedbuf_size": "1e4",
                            "leftover_commod": "reprocess_waste2",
                            "leftoverbuf_size": "1e4",
                            "streams": {
                                "item": [
                                    {
                                        "commod": "separations2Pu",
                                        "info": {"buf_size": "1e4", "efficiencies": {"item": {"comp": "Pu", "eff": "1"}}}
                                    },
                                    {
                                        "commod": "separations2U",
                                        "info": {"buf_size": "1e4", "efficiencies": {"item": {"comp": "U", "eff": "1"}}}
                                    }
                                ]
                            },
                            "throughput": "1e4"
                        }
                    },
                    "name": "separations2"
                },
                {
                    "config": {
                        "Sink": {
                            "in_commods": {"val": ["reprocess_waste1", "reprocess_waste2"]},
                            "max_inv_size": "1e4"
                        }
                    },
                    "name": "sink"
                }
            ],
            "recipe": [
                {
                    "basis": "mass",
                    "name": "source_recipe",
                    "nuclide": [{"comp": "0.5", "id": "U235"}, {"comp": "0.5", "id": "Pu238"}]
                },
                {
                    "basis": "mass",
                    "name": "reactor_recipe",
                    "nuclide": [{"comp": "0.5", "id": "U235"}, {"comp": "0.5", "id": "Pu238"}]
                }
            ],
            "region": {
                "config": {"NullRegion": "\n      "},
                "institution": [
                    {
                        "config": {
                            "DemandDrivenDeploymentInst": {
                                "calc_method": calc_method,
                                "facility_commod": {
                                    "item": [
                                        {"commod": "POWER", "facility": "reactor2"},
                                        {"commod": "POWER", "facility": "reactor1"},
                                        {"commod": "sourceoutput", "facility": "source"}
                                    ]
                                },
                                "facility_capacity": {
                                    "item": [
                                        {"capacity": "3e3", "facility": "reactor2"},
                                        {"capacity": "3e3", "facility": "reactor1"},
                                        {"capacity": "3e3", "facility": "source"}
                                    ]
                                },
                                "facility_pref": {
                                    "item": [
                                        {"pref": "2*t", "facility": "reactor2"},
                                        {"pref": "t", "facility": "reactor1"}
                                    ]
                                },
                                "facility_constraintcommod": {
                                    "item": [
                                        {"constraintcommod": "mixeroutput", "facility": "reactor2"}
                                    ]
                                },
                                "facility_constraintval": {
                                    "item": [
                                        {"constraintval": "8000", "facility": "reactor2"}
                                    ]
                                },
                                "demand_eq": "1000*t",
                                "record": "1",
                                "steps": "1"
                            }
                        },
                        "name": "demand_inst"
                    },
                    {
                        "config": {
                            "SupplyDrivenDeploymentInst": {
                                "calc_method": calc_method,
                                "capacity_std_dev": "1.0",
                                "facility_commod": {
                                    "item": [
                                        {"commod": "reactor1output", "facility": "separations1"},
                                        {"commod": "separations1Pu", "facility": "mixer"},
                                        {"commod": "reactor2output", "facility": "separations2"}
                                    ]
                                },
                                "facility_capacity": {
                                    "item": [
                                        {"capacity": "1e4", "facility": "separations1"},
                                        {"capacity": "1e4", "facility": "mixer"},
                                        {"capacity": "1e4", "facility": "separations2"}
                                    ]
                                },
                                "record": "1",
                                "steps": "1"
                            }
                        },
                        "name": "supply_inst"
                    }
                ],
                "name": "SingleRegion"
            }
        }
    }

# initialize metric dict
metric_dict = {}
for calc_method in calc_methods:
    name = "scenario_7_input_" + calc_method
    input_file = name + ".json"
    output_file = name + ".sqlite"
    with open(input_file, 'w') as f:
        json.dump(scenario_7_input[calc_method], f)
    s = subprocess.check_output(['cyclus', '-o', output_file, input_file],
                                universal_newlines=True, env=ENV)
    # Initialize dicts
    all_dict = {}
    agent_entry_dict = {}
    all_dict['power'] = tester.supply_demand_dict_driving(
        output_file, demand_eq, 'power')
    all_dict['sourceoutput'] = tester.supply_demand_dict_nondriving(
        output_file, 'sourceoutput', True)
    all_dict['reactor1output'] = tester.supply_demand_dict_nondriving(
        output_file, 'reactor1output', False)
    all_dict['separations1Pu'] = tester.supply_demand_dict_nondriving(
        output_file, 'separations1Pu', False)
    all_dict['reactor2output'] = tester.supply_demand_dict_nondriving(
        output_file, 'reactor2output', False)

    agent_entry_dict['power'] = tester.get_agent_dict(
        output_file, ['reactor1', 'reactor2'])
    agent_entry_dict['sourceoutput'] = tester.get_agent_dict(output_file, [
                                                             'source'])
    agent_entry_dict['reactor1output'] = tester.get_agent_dict(output_file, [
                                                               'separations1'])
    agent_entry_dict['separations1Pu'] = tester.get_agent_dict(output_file, [
                                                               'mixer'])
    agent_entry_dict['reactor2output'] = tester.get_agent_dict(output_file, [
                                                               'separations2'])

    # plots demand, supply, calculated demand, calculated supply for the
    # scenario for each calc method
    name1 = "scenario_7_input_" + calc_method + "_power"
    plotter.plot_demand_supply_agent(
        all_dict['power'],
        agent_entry_dict['power'],
        'power',
        name1,
        True,
        False,
        False)
    name2 = "scenario_7_input_" + calc_method + "_sourceoutput"
    plotter.plot_demand_supply_agent(
        all_dict['sourceoutput'],
        agent_entry_dict['sourceoutput'],
        'sourceoutput',
        name2,
        True,
        False,
        False)
    name3 = "scenario_7_input_" + calc_method + "_reactor1output"
    plotter.plot_demand_supply_agent(
        all_dict['reactor1output'],
        agent_entry_dict['reactor1output'],
        'reactor1output',
        name3,
        False,
        False,
        False)
    name4 = "scenario_7_input_" + calc_method + "_separations1Pu"
    plotter.plot_demand_supply_agent(
        all_dict['separations1Pu'],
        agent_entry_dict['separations1Pu'],
        'separations1Pu',
        name4,
        False,
        False,
        False)
    name5 = "scenario_7_input_" + calc_method + "_reactor2output"
    plotter.plot_demand_supply_agent(
        all_dict['reactor2output'],
        agent_entry_dict['reactor1output'],
        'reactor2output',
        name5,
        False,
        False,
        False)

    metric_dict = tester.metrics(
        all_dict['power'],
        metric_dict,
        calc_method,
        'power',
        True)
    metric_dict = tester.metrics(
        all_dict['sourceoutput'],
        metric_dict,
        calc_method,
        'sourceoutput',
        True)
    metric_dict = tester.metrics(
        all_dict['reactor1output'],
        metric_dict,
        calc_method,
        'reactor1output',
        False)
    metric_dict = tester.metrics(
        all_dict['separations1Pu'],
        metric_dict,
        calc_method,
        'separations1Pu',
        False)
    metric_dict = tester.metrics(
        all_dict['reactor2output'],
        metric_dict,
        calc_method,
        'reactor2output',
        False)

    df = pd.DataFrame(metric_dict)
    df.to_csv('scenario_7_output.csv')
