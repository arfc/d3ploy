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
import d3ploy.tester as functions
import d3ploy.plotter as plotter
import collections

# Delete previously generated files
direc = os.listdir('./')
hit_list = glob.glob('*.sqlite') + glob.glob('*.json') + glob.glob('*.png')
for file in hit_list:
    os.remove(file)

ENV = dict(os.environ)
ENV['PYTHONPATH'] = ".:" + ENV.get('PYTHONPATH', '')


##### List of types of calc methods that are to be tested #####
calc_methods = ["ma", "arma", "arch", "poly",
                "exp_smoothing", "holt_winters", "fft"]

######################################SCENARIO 5##########################################
# scenario 5, source -> reactor (cycle time = 1, refuel time = 0) -> sink
scenario_5_input = {}
demand_eq = "1000*t"

for calc_method in calc_methods:
    scenario_5_input[calc_method] = {
 "simulation": {
  "archetypes": {
   "spec": [
    {"lib": "agents", "name": "NullRegion"},
    {"lib": "cycamore", "name": "Source"},
    {"lib": "cycamore", "name": "Reactor"},
    {"lib": "cycamore", "name": "Sink"},
    {"lib": "d3ploy.timeseries_inst", "name": "TimeSeriesInst"},
    {"lib": "d3ploy.supply_driven_deployment_inst", "name": "SupplyDrivenDeploymentInst"}
   ]
  },
  "control": {"duration": "100", "startmonth": "1", "startyear": "2000"},
  "facility": [
   {
    "config": {
     "Source": {"outcommod": "fuel", "outrecipe": "fresh_uox", "throughput": "3000"}
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
  ],
  "region": {
   "config": {"NullRegion": "\n      "},
   "institution": [
    {
     "config": {
      "TimeSeriesInst": {
       "calc_method": calc_method,
       "commodities": {"val": ["fuel_source_3000", "POWER_reactor_1000"]},
       "demand_eq": demand_eq,
       "demand_std_dev": "1.0",
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
       "calc_method": "ma",
       "commodities": {"val": "spentfuel_sink_100000"},
       "capacity_std_dev": "1.0",
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

metric_dict = collections.OrderedDict(
    {'spentfuel_residuals': {}, 'spentfuel_chi2': {}, 'spentfuel_undersupply': {},
        'POWER_residuals': {}, 'POWER_chi2': {}, 'POWER_undersupply': {},
     'fuel_residuals': {}, 'fuel_chi2': {}, 'fuel_undersupply': {}})


for calc_method in calc_methods:
    name = "scenario_5_input_" + calc_method
    input_file = name + ".json"
    output_file = name + ".sqlite"
    with open(input_file, 'w') as f:
        json.dump(scenario_5_input[calc_method], f)

    s = subprocess.check_output(['cyclus', '-o', output_file, input_file],
                                universal_newlines=True, env=ENV)

    dict_demand, dict_supply, dict_calc_demand, dict_calc_supply = functions.supply_demand_dict_driving(
        output_file, demand_eq, 'power')

    dict_demand2, dict_supply2, dict_calc_demand2, dict_calc_supply2 = functions.supply_demand_dict_nondriving(
        output_file, 'fuel',True)
    
    dict_demand3, dict_supply3, dict_calc_demand3, dict_calc_supply3 = functions.supply_demand_dict_nondriving(
        output_file, 'spentfuel',False)
    # plots demand, supply, calculated demand, calculated supply for the scenario for each calc method
    plotter.plot_demand_supply(
        dict_demand, dict_supply, dict_calc_demand, dict_calc_supply, 'power', name, True)
    name2 = "scenario_5_input_"+ calc_method +"_fuel"
    plotter.plot_demand_supply(
        dict_demand2, dict_supply2, dict_calc_demand2, dict_calc_supply2, 'fuel', name2, True)
    name3 = "scenario_5_input_"+ calc_method +"_spentfuel"
    plotter.plot_demand_supply(
        dict_demand3, dict_supply3, dict_calc_demand3, dict_calc_supply3, 'spentfuel', name3, False)

    metric_dict['POWER_residuals'][calc_method] = functions.residuals(dict_demand, dict_supply)
    metric_dict['POWER_chi2'][calc_method] = functions.chi_goodness_test(dict_demand, dict_supply)
    metric_dict['POWER_undersupply'][calc_method] = functions.supply_under_demand(
        dict_demand, dict_supply, True)

    metric_dict['fuel_residuals'][calc_method] = functions.residuals(
        dict_demand2, dict_supply2)
    metric_dict['fuel_chi2'][calc_method] = functions.chi_goodness_test(
        dict_demand2, dict_supply2)
    metric_dict['fuel_undersupply'][calc_method] = functions.supply_under_demand(
        dict_demand2, dict_supply2, True)

    metric_dict['spentfuel_residuals'][calc_method] = functions.residuals(
        dict_demand3, dict_supply3)
    metric_dict['spentfuel_chi2'][calc_method] = functions.chi_goodness_test(
        dict_demand3, dict_supply3)
    metric_dict['spentfuel_undersupply'][calc_method] = functions.supply_under_demand(
        dict_demand3, dict_supply3, False)
        
    df = pd.DataFrame(metric_dict)
    df.to_csv('scenario_5_output.csv')
