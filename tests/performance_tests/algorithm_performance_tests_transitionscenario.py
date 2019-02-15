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
hit_list = glob.glob('*.json') + glob.glob('*.png') + glob.glob('*.csv') + glob.glob('*.txt')
for file in hit_list:
    os.remove(file)

ENV = dict(os.environ)
ENV['PYTHONPATH'] = ".:" + ENV.get('PYTHONPATH', '')


######################################TRANSITION SCENARIO 1##########################################

# initialize metric dict
demand_eq = '60000'
calc_method = 'ma'
name = "transitionscenario_1_input"
output_file = name + ".sqlite"
# Initialize dicts  
metric_dict = {}
all_dict = {}
agent_entry_dict = {}


# get agent deployment
commod_dict = {'enrichmentout': ['enrichment'],
               'sourceout': ['source'],
               'power': ['lwr', 'fr'],
               'lwrstorageout': ['lwrreprocessing'],
               'frstorageout': ['frreprocessing'],
               'lwrout': ['lwrstorage'],
               'frout': ['frstorage'],
               'lwrreprocessingoutpu': ['pumixerlwr'],
               'frreprocessingoutpu' : ['pumixerfr'],
               'lwrreprocessingwaste': ['lwrsink'],
               'frreprocessingwaste': ['frsink']}
for commod, facility in commod_dict.items():
    agent_entry_dict[commod] = tester.get_agent_dict(output_file, facility)
###########################

# get supply deamnd dict
# and plot
all_dict['power'] = tester.supply_demand_dict_driving(
    output_file, demand_eq, 'power')
plotter.plot_demand_supply_agent(all_dict['power'], agent_entry_dict['power'], 'power',
                                 'transitionscenario_1_input_power', True)

front_commods = ['sourceout', 'enrichmentout']
back_commods = ['lwrstorageout',
                'frstorageout', 'lwrout', 'frout', 'lwrreprocessingoutpu',
                'frreprocessingoutpu', 'lwrreprocessingwaste', 'frreprocessingwaste']
for commod in front_commods:
    all_dict[commod] = tester.supply_demand_dict_nondriving(output_file,
                        commod, True)
    name = 'transitionscenario_1_input_' + commod
    plotter.plot_demand_supply_agent(all_dict[commod], agent_entry_dict[commod],
                                     commod, name, True)
    metric_dict = tester.metrics(
        all_dict[commod], metric_dict, calc_method, commod, True)

for commod in back_commods:
    all_dict[commod] = tester.supply_demand_dict_nondriving(output_file,
                        commod, False)
    name = 'transitionscenario_1_input_' + commod
    plotter.plot_demand_supply_agent(all_dict[commod], agent_entry_dict[commod],
                                     commod, name, False)
    metric_dict = tester.metrics(
        all_dict[commod], metric_dict, calc_method, commod, False)

#print(all_dict['frout'])

###########################

df = pd.DataFrame(metric_dict)
df.to_csv('transitionscenario_1_output.csv')
