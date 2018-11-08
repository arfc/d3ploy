"""
This python file contains fleet based unit tests for timeseries_inst archetype for DO_solvers.

"""

import json
import re
import subprocess
import os
import sqlite3 as lite
import pytest
import copy
import glob
import sys
from matplotlib import pyplot as plt
import numpy as np
import test_support_functions as functions

from nose.tools import assert_in, assert_true, assert_equals

# Delete previously generated files
direc = os.listdir('./')
hit_list = glob.glob('*.sqlite') + glob.glob('*.json') + glob.glob('*.png')
for file in hit_list:
    os.remove(file)

ENV = dict(os.environ)
ENV['PYTHONPATH'] = ".:" + ENV.get('PYTHONPATH', '')


# List of types of calc methods that are to be tested 
calc_methods = ["ma","arma","poly","exp_smoothing","holt_winters"]

######################################SCENARIO 1################################################
scenario_1_input = {}
demand_eq = "100*t"

for x in range(0,len(calc_methods)):
    scenario_1_input[x] = {
        "simulation": {
            "archetypes": {
                "spec": [
                    {"lib": "agents", "name": "NullRegion"},
                    {"lib": "cycamore", "name": "Source"},
                    {"lib": "cycamore", "name": "Reactor"},
                    {"lib": "cycamore", "name": "Sink"},
                    {"lib": "d3ploy.timeseries_inst", "name": "TimeSeriesInst"}
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
            ],
            "facility": [{
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
            }],
            "region": {
                "config": {"NullRegion": "\n      "},
                "institution": {
                    "config": {
                        "TimeSeriesInst": {
                            "calc_method": calc_methods[x],
                            "commodities": {"val": ["fuel_source_3000"]},
                            "driving_commod": "fuel",
                            "demand_std_dev": "1.0",
                            "demand_eq": demand_eq,
                            "record": "1",
                            "steps": "1"
                        }
                    },
                    "name": "source_inst"
                },
                "name": "SingleRegion"
            }
        }
    }
def scenario_1(): 
    dict_total = {}
    dict_negative = {}

    for x in range(0,len(calc_methods)):
        name = "scenario_1_input_"+calc_methods[x]
        input_file = name+".json"
        output_file = name+".sqlite"
        with open(input_file, 'w') as f:
            json.dump(scenario_1_input[x], f)
        s = subprocess.check_output(['cyclus', '-o', output_file, input_file],
                                    universal_newlines=True, env=ENV)

        dict_demand, dict_supply, dict_calc_demand, dict_calc_supply = functions.supply_demand_dict_driving(output_file,demand_eq,'fuel')
        # plots demand, supply, calculated demand, calculated supply for the scenario for each calc method 
        functions.plot_demand_supply(dict_demand, dict_supply, dict_calc_demand, dict_calc_supply,demand_eq,name)

        dict_total[x], dict_negative[x] = functions.calculate_total_neg(dict_demand, dict_supply)


    # tells you which is the best calc method based on normalizing and scoring
    calc_method_num, score = functions.find_best(dict_total,dict_negative)
    best_calc_method = calc_methods[calc_method_num]
    print('SCENARIO1',best_calc_method)

    number_within_tolerance = functions.supply_within_demand_fac_tol(output_file,'a-grow-1',2)
    print(number_within_tolerance)
    assert(number_within_tolerance == 0)

    

######################################SCENARIO 2################################################
scenario_2_input = {}
demand_eq = "100*t"

for x in range(0,len(calc_methods)):
    scenario_2_input[x] = {
        "simulation": {
            "archetypes": {
                "spec": [
                    {"lib": "agents", "name": "NullRegion"},
                    {"lib": "cycamore", "name": "Source"},
                    {"lib": "cycamore", "name": "Reactor"},
                    {"lib": "cycamore", "name": "Sink"},
                    {"lib": "d3ploy.timeseries_inst", "name": "TimeSeriesInst"}
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
            ],
            "facility": [{
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
            }],
            "region": {
                "config": {"NullRegion": "\n      "},
                "institution": {
                    "config": {
                        "TimeSeriesInst": {
                            "calc_method": calc_methods[x],
                            "commodities": {"val": ["fuel_source_3000","POWER_reactor_1000"]},
                            "driving_commod": "POWER",
                            "demand_std_dev": "1.0",
                            "demand_eq": demand_eq,
                            "record": "1",
                            "steps": "1"
                        }
                    },
                    "name": "source_inst"
                },
                "name": "SingleRegion"
            }
        }
    }

dict_total = {}
dict_negative = {}
dict_total2 = {}
dict_negative2 = {}

for x in range(0,len(calc_methods)):
    name = "scenario_2_input_"+calc_methods[x]
    input_file = name+".json"
    output_file = name+".sqlite"
    with open(input_file, 'w') as f:
        json.dump(scenario_2_input[x], f)
    s = subprocess.check_output(['cyclus', '-o', output_file, input_file],
                                universal_newlines=True, env=ENV)

    dict_demand, dict_supply, dict_calc_demand, dict_calc_supply = functions.supply_demand_dict_driving(output_file,demand_eq,'power')
    dict_demand2, dict_supply2, dict_calc_demand2, dict_calc_supply2 = functions.supply_demand_dict_nondriving(output_file,'fuel')
    # plots demand, supply, calculated demand, calculated supply for the scenario for each calc method 
    functions.plot_demand_supply(dict_demand, dict_supply, dict_calc_demand, dict_calc_supply,'power',name)
    name2 = "scenario_2_input_"+calc_methods[x]+"fuel"
    functions.plot_demand_supply(dict_demand2, dict_supply2, dict_calc_demand2, dict_calc_supply2,'fuel',name2)
    dict_total[x], dict_negative[x] = functions.calculate_total_neg(dict_demand, dict_supply)
    dict_total2[x], dict_negative2[x] = functions.calculate_total_neg(dict_demand2, dict_supply2)

# tells you which is the best calc method based on normalizing and scoring
print(dict_total)
print(dict_negative)
calc_method_num, score = functions.find_best(dict_total,dict_negative)
best_calc_method = calc_methods[calc_method_num]
print('POWER',best_calc_method)
print('POWER score',score)


print(dict_total2)
print(dict_negative2)
calc_method_num2, score2 = functions.find_best(dict_total2,dict_negative2)
best_calc_method2 = calc_methods[calc_method_num2]
print('FUEL',best_calc_method2)
print('FUEL score',score2)