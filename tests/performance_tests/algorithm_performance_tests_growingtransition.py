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
hit_list = glob.glob('*.json') + glob.glob('*.png') + \
    glob.glob('*.csv') + glob.glob('*.txt') + glob.glob('*.sqlite')
for file in hit_list:
    os.remove(file)

ENV = dict(os.environ)
ENV['PYTHONPATH'] = ".:" + ENV.get('PYTHONPATH', '')


output_file = 'growing_transition.sqlite'
input_path = os.path.abspath(__file__)
find = 'd3ploy/'
indx = input_path.rfind('d3ploy/')
input = input_path.replace(
    input_path[indx + len(find):], 'input/growing_transition.xml')
s = subprocess.check_output(['cyclus', '-o', output_file, input],
                            universal_newlines=True, env=ENV)

demand_eq = '10000/(1+np.exp(t-40))+250*t/(1+np.exp(40-t))'
name = 'scenario'

# Initialize dicts
all_dict_power = {}
all_dict_fuel = {}
all_dict_spent_fuel = {}
agent_entry_dict = {}
metric_dict = {}

all_dict_power = tester.supply_demand_dict_driving(
    output_file, demand_eq, 'power')
all_dict_fuel = tester.supply_demand_dict_nondriving(
    output_file, 'fuel', True)
all_dict_spent_fuel = tester.supply_demand_dict_nondriving(
    output_file, 'spent_fuel', False)

agent_entry_dict['power'] = tester.get_agent_dict(
    output_file,
    [
        'reactor1',
        'reactor2',
        'reactor3',
        'reactor4',
        'reactor5',
        'reactor6',
        'reactor7',
        'reactor8',
        'reactor9',
        'reactor10',
        'newreactor'])
agent_entry_dict['fuel'] = tester.get_agent_dict(
    output_file, ['source', 'initialsource'])
agent_entry_dict['spent_fuel'] = tester.get_agent_dict(
    output_file, ['lwrsink'])
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
plotter.plot_demand_supply_agent(
    all_dict_spent_fuel,
    agent_entry_dict['spent_fuel'],
    'spent_fuel',
    name + '_spent_fuel',
    False,
    False,
    False)

calc_method = 'scenario'

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
    all_dict_spent_fuel,
    metric_dict,
    calc_method,
    'spent_fuel',
    False)

df = pd.DataFrame(metric_dict)
df.to_csv('scenario.csv')
