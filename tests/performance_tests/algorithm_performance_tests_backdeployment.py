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
                {"lib": "cycamore", "name": "Storage"},
                {"lib": "d3ploy.demand_driven_deployment_inst", "name": "DemandDrivenDeploymentInst"},
                {
                    "lib": "d3ploy.supply_driven_deployment_inst",
                    "name": "SupplyDrivenDeploymentInst"
                }
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
        ]}
}
"""
######################################SCENARIO 5##########################
# scenario 5, source -> reactor (cycle time = 1, refuel time = 0) -> sink
scenario_5_input = {}
demand_eq = "1000*t"

for calc_method in calc_methods:
    scenario_5_input[calc_method] = copy.deepcopy(scenario_template)
    scenario_5_input[calc_method]["simulation"].update({"facility": [
        {
            "config": {
                "Source": {"outcommod": "fuel", "outrecipe": "fresh_uox", "throughput": "3e3"}
            },
            "name": "source"
        },
        {
            "config": {"Sink": {"in_commods": {"val": "spentfuel"}, "max_inv_size": "1e6"}},
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
                    "refuel_time": "0"
                }
            },
            "name": "reactor"
        }
    ],
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
    ]})
    scenario_5_input[calc_method]["simulation"].update({"region": {
        "config": {"NullRegion": "\n      "},
        "institution": [
            {
                "config": {
                    "DemandDrivenDeploymentInst": {
                        "calc_method": calc_method,
                        "facility_commod": {
                            "item": [
                                {"commod": "POWER", "facility": "reactor"},
                                {"commod": "fuel", "facility": "source"}
                            ]
                        },
                        "facility_capacity": {
                            "item": [
                                {"capacity": "1e3", "facility": "reactor"},
                                {"capacity": "3e3", "facility": "source"}
                            ]
                        },
                        "demand_eq": demand_eq,
                        "driving_commod": "POWER",
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
                        "facility_commod": {
                            "item": [
                                {"commod": "spentfuel", "facility": "sink"}
                            ]
                        },
                        "facility_capacity": {
                            "item": [
                                {"capacity": "1e6", "facility": "sink"}
                            ]
                        },
                        "capacity_std_dev": "1.0",
                        "record": "1",
                        "steps": "1"
                    }
                },
                "name": "supply_inst"
            }
        ],
        "name": "SingleRegion"
    }})

# initialize metric dict
metric_dict = {}

for calc_method in calc_methods:
    name = "scenario_5_input_" + calc_method
    input_file = name + ".json"
    output_file = name + ".sqlite"
    with open(input_file, 'w') as f:
        json.dump(scenario_5_input[calc_method], f)

    s = subprocess.check_output(['cyclus', '-o', output_file, input_file],
                                universal_newlines=True, env=ENV)

    # Initialize dicts
    all_dict_power = {}
    all_dict_fuel = {}
    all_dict_spentfuel = {}
    agent_entry_dict = {}

    all_dict_power = tester.supply_demand_dict_driving(
        output_file, demand_eq, 'power')
    all_dict_fuel = tester.supply_demand_dict_nondriving(
        output_file, 'fuel', True)
    all_dict_spentfuel = tester.supply_demand_dict_nondriving(
        output_file, 'spentfuel', False)

    agent_entry_dict['power'] = tester.get_agent_dict(output_file, ['reactor'])
    agent_entry_dict['fuel'] = tester.get_agent_dict(output_file, ['source'])
    agent_entry_dict['spentfuel'] = tester.get_agent_dict(output_file, [
                                                          'sink'])

    # plots demand, supply, calculated demand, calculated supply for the
    # scenario for each calc method
    plotter.plot_demand_supply_agent(
        all_dict_power,
        agent_entry_dict['power'],
        'power',
        name + "_power",
        True,
        False,
        False)
    plotter.plot_demand_supply_agent(
        all_dict_fuel,
        agent_entry_dict['fuel'],
        'fuel',
        name + "_fuel",
        True,
        False,
        False)
    plotter.plot_demand_supply_agent(
        all_dict_spentfuel,
        agent_entry_dict['spentfuel'],
        'spentfuel',
        name + "_spentfuel",
        False,
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
    metric_dict = tester.metrics(
        all_dict_spentfuel,
        metric_dict,
        calc_method,
        'spentfuel',
        False)

    df = pd.DataFrame(metric_dict)
    df.to_csv('scenario_5_output.csv')


######################################SCENARIO 6##########################
# scenario 6, source -> reactor (cycle time = 1, refuel time = 0) ->
# storage -> sink
scenario_6_input = {}
demand_eq = "1000*t"

for calc_method in calc_methods:
    scenario_6_input[calc_method] = copy.deepcopy(scenario_template)
    scenario_6_input[calc_method]["simulation"].update({"facility": [
        {
            "config": {
                "Source": {"outcommod": "fuel", "outrecipe": "fresh_uox", "throughput": "3e3"}
            },
            "name": "source"
        },
        {
            "config": {"Sink": {"in_commods": {"val": "coolspentfuel"}, "max_inv_size": "1e6"}},
            "name": "sink"
        },
        {
            "config": {
                "Storage": {
                    "in_commods": {"val": "spentfuel"},
                    "max_inv_size": "1e6",
                    "out_commods": {"val": "coolspentfuel"},
                    "residence_time": "3",
                    "throughput": "1e6"
                }
            },
            "name": "storage"
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
                    "refuel_time": "0"
                }
            },
            "name": "reactor"
        }
    ]})
    scenario_6_input[calc_method]["simulation"].update({"region": {
        "config": {"NullRegion": "\n      "},
        "institution": [
            {
                "config": {
                    "DemandDrivenDeploymentInst": {
                        "calc_method": calc_method,
                        "facility_commod": {
                            "item": [
                                {"commod": "POWER", "facility": "reactor"},
                                {"commod": "fuel", "facility": "source"}
                            ]
                        },
                        "facility_capacity": {
                            "item": [
                                {"capacity": "3e3", "facility": "source"},
                                {"capacity": "1e3", "facility": "reactor"}
                            ]
                        },
                        "demand_eq": "1000*t",
                        "driving_commod": "POWER",
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
                                {"commod": "spentfuel", "facility": "storage"},
                                {"commod": "coolspentfuel", "facility": "sink"}
                            ]
                        },
                        "facility_capacity": {
                            "item": [
                                {"capacity": "1e6", "facility": "storage"},
                                {"capacity": "1e6", "facility": "sink"}
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
    }})

metric_dict = {}

for calc_method in calc_methods:
    name = "scenario_6_input_" + calc_method
    input_file = name + ".json"
    output_file = name + ".sqlite"
    with open(input_file, 'w') as f:
        json.dump(scenario_6_input[calc_method], f)

    s = subprocess.check_output(['cyclus', '-o', output_file, input_file],
                                universal_newlines=True, env=ENV)

    # Initialize dicts
    all_dict_power = {}
    all_dict_fuel = {}
    all_dict_spentfuel = {}
    all_dict_coolspentfuel = {}
    agent_entry_dict = {}

    all_dict_power = tester.supply_demand_dict_driving(
        output_file, demand_eq, 'power')
    all_dict_fuel = tester.supply_demand_dict_nondriving(
        output_file, 'fuel', True)
    all_dict_spentfuel = tester.supply_demand_dict_nondriving(
        output_file, 'spentfuel', False)
    all_dict_coolspentfuel = tester.supply_demand_dict_nondriving(
        output_file, 'coolspentfuel', False)

    agent_entry_dict['power'] = tester.get_agent_dict(output_file, ['reactor'])
    agent_entry_dict['fuel'] = tester.get_agent_dict(output_file, ['source'])
    agent_entry_dict['coolspentfuel'] = tester.get_agent_dict(output_file, [
                                                              'sink'])
    agent_entry_dict['spentfuel'] = tester.get_agent_dict(output_file, [
                                                          'storage'])

    # plots demand, supply, calculated demand, calculated supply for the
    # scenario for each calc method
    plotter.plot_demand_supply_agent(
        all_dict_power,
        agent_entry_dict['power'],
        'power',
        name + "_power",
        True,
        False,
        False)
    plotter.plot_demand_supply_agent(
        all_dict_fuel,
        agent_entry_dict['fuel'],
        'fuel',
        name + "_fuel",
        True,
        False,
        False)
    plotter.plot_demand_supply_agent(
        all_dict_spentfuel,
        agent_entry_dict['spentfuel'],
        'spentfuel',
        name + "_spentfuel",
        False,
        False,
        False)
    plotter.plot_demand_supply_agent(
        all_dict_coolspentfuel,
        agent_entry_dict['coolspentfuel'],
        'coolspentfuel',
        name + "_coolspentfuel",
        False,
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
    metric_dict = tester.metrics(
        all_dict_spentfuel,
        metric_dict,
        calc_method,
        'spentfuel',
        False)
    metric_dict = tester.metrics(
        all_dict_coolspentfuel,
        metric_dict,
        calc_method,
        'coolspentfuel',
        False)

    df = pd.DataFrame(metric_dict)
    df.to_csv('scenario_6_output.csv')

"""
######################################SCENARIO 7##########################
# scenario 7, source -> reactor (cycle time = 18, refuel time = 0) -> sink
scenario_7_input = {}
demand_eq = "1000*t"

for calc_method in calc_methods:
    scenario_7_input[calc_method] = copy.deepcopy(scenario_template)
    scenario_7_input[calc_method]["simulation"].update({"facility": [
        {
            "config": {
                "Source": {"outcommod": "fuel", "outrecipe": "fresh_uox", "throughput": "3e3"}
            },
            "name": "source"
        },
        {
            "config": {"Sink": {"in_commods": {"val": "spentfuel"}, "max_inv_size": "1e6"}},
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
                    "refuel_time": "1"
                }
            },
            "name": "reactor"
        }
    ],
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
    ]})
    scenario_7_input[calc_method]["simulation"].update({"region": {
        "config": {"NullRegion": "\n      "},
        "institution": [
            {
                "config": {
                    "DemandDrivenDeploymentInst": {
                        "calc_method": calc_method,
                        "facility_commod": {
                            "item": [
                                {"commod": "POWER", "facility": "reactor"},
                                {"commod": "fuel", "facility": "source"}
                            ]
                        },
                        "facility_capacity": {
                            "item": [
                                {"capacity": "1e3", "facility": "reactor"},
                                {"capacity": "3e3", "facility": "source"}
                            ]
                        },
                        "demand_eq": demand_eq,
                        "driving_commod": "POWER",
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
                        "facility_commod": {
                            "item": [
                                {"commod": "spentfuel", "facility": "sink"}
                            ]
                        },
                        "facility_capacity": {
                            "item": [
                                {"capacity": "1e6", "facility": "sink"}
                            ]
                        },
                        "capacity_std_dev": "1.0",
                        "record": "1",
                        "steps": "1"
                    }
                },
                "name": "supply_inst"
            }
        ],
        "name": "SingleRegion"
    }})

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
    all_dict_power = {}
    all_dict_fuel = {}
    all_dict_spentfuel = {}
    agent_entry_dict = {}

    all_dict_power = tester.supply_demand_dict_driving(
        output_file, demand_eq, 'power')
    all_dict_fuel = tester.supply_demand_dict_nondriving(
        output_file, 'fuel', True)
    all_dict_spentfuel = tester.supply_demand_dict_nondriving(
        output_file, 'spentfuel', False)

    agent_entry_dict['power'] = tester.get_agent_dict(output_file, ['reactor'])
    agent_entry_dict['fuel'] = tester.get_agent_dict(output_file, ['source'])
    agent_entry_dict['spentfuel'] = tester.get_agent_dict(output_file, [
                                                          'sink'])

    # plots demand, supply, calculated demand, calculated supply for the
    # scenario for each calc method
    plotter.plot_demand_supply_agent(
        all_dict_power,
        agent_entry_dict['power'],
        'power',
        name + "_power",
        True,
        False,
        False)
    plotter.plot_demand_supply_agent(
        all_dict_fuel,
        agent_entry_dict['fuel'],
        'fuel',
        name + "_fuel",
        True,
        False,
        False)
    plotter.plot_demand_supply_agent(
        all_dict_spentfuel,
        agent_entry_dict['spentfuel'],
        'spentfuel',
        name + "_spentfuel",
        False,
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
    metric_dict = tester.metrics(
        all_dict_spentfuel,
        metric_dict,
        calc_method,
        'spentfuel',
        False)

    df = pd.DataFrame(metric_dict)
    df.to_csv('scenario_7_output.csv')
