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
demand_eq = '60'
calc_method = 'ma'
name = "transitionscenario_1_input"
output_file = name + ".sqlite"
# Initialize dicts  
metric_dict = {}
all_dict = {}
agent_entry_dict = {}
all_dict['power'] = tester.supply_demand_dict_driving(
    output_file, demand_eq, 'power')
all_dict['sourceout'] = tester.supply_demand_dict_nondriving(
    output_file, 'sourceout',True)
all_dict['enrichmentout'] = tester.supply_demand_dict_nondriving(
    output_file, 'enrichmentout',True)    

agent_entry_dict['power'] = tester.get_agent_dict(output_file, ['lwr', 'fr'])
agent_entry_dict['sourceout'] = tester.get_agent_dict(output_file, ['source'])
agent_entry_dict['enrichmentout'] = tester.get_agent_dict(output_file, ['enrichment'])

# plots demand, supply, calculated demand, calculated supply for the scenario for each calc method
name1 = "transitionscenario_1_input_power"
plotter.plot_demand_supply_agent(all_dict['power'], agent_entry_dict['power'], 'power', name1, True)
name2 = "transitionscenario_1_input_sourceout"
plotter.plot_demand_supply_agent(all_dict['sourceout'], agent_entry_dict['sourceout'],
                                    'sourceout', name2, True)
name3 = "transitionscenario_1_input_enrichmentout"
plotter.plot_demand_supply_agent(all_dict['enrichmentout'], agent_entry_dict['enrichmentout'],
                                    'enrichmentout', name3, True)


metric_dict = tester.metrics(all_dict['power'],metric_dict,calc_method,'power',True)
metric_dict = tester.metrics(all_dict['sourceout'],metric_dict,calc_method,'sourceout',True)
metric_dict = tester.metrics(all_dict['enrichmentout'],metric_dict,calc_method,'enrichmentout',True)
    
df = pd.DataFrame(metric_dict)
df.to_csv('transitionscenario_1_output.csv')