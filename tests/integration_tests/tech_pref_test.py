"""
This python file contains tech pref capability tests for TimeSeriesInst
archetype. 
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
import d3ploy.tester as functions

from nose.tools import assert_in, assert_true, assert_equals

# Delete previously generated files
direc = os.listdir('./')
hit_list = glob.glob('*.sqlite') + glob.glob('*.json') + glob.glob('*.png')
for file in hit_list:
    os.remove(file)

ENV = dict(os.environ)
ENV['PYTHONPATH'] = ".:" + ENV.get('PYTHONPATH', '')


input = {
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
  "control": {"duration": "50", "startmonth": "1", "startyear": "2000"},
  "facility": [
   {
    "config": {"Source": {"outcommod": "fuel", "outrecipe": "fresh_uox", "throughput": "1"}},
    "name": "source"
   },
   {
    "config": {"Sink": {"in_commods": {"val": "spent_uox"}, "max_inv_size": "10"}},
    "name": "sink"
   },
   {
    "config": {
     "Reactor": {
      "assem_size": "1",
      "cycle_time": "1",
      "fuel_incommods": {"val": "fuel"},
      "fuel_inrecipes": {"val": "fresh_uox"},
      "fuel_outcommods": {"val": "spent_uox"},
      "fuel_outrecipes": {"val": "spent_uox"},
      "n_assem_batch": "1",
      "n_assem_core": "1",
      "power_cap": "1",
      "refuel_time": "0"
     }
    },
    "name": "reactor1"
   },
   {
    "config": {
     "Reactor": {
      "assem_size": "1",
      "cycle_time": "1",
      "fuel_incommods": {"val": "fuel"},
      "fuel_inrecipes": {"val": "fresh_uox"},
      "fuel_outcommods": {"val": "spent_uox"},
      "fuel_outrecipes": {"val": "spent_uox"},
      "n_assem_batch": "1",
      "n_assem_core": "1",
      "power_cap": "1",
      "refuel_time": "0"
     }
    },
    "name": "reactor2"
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
   "institution": {
    "config": {
     "TimeSeriesInst": {
      "calc_method": "poly",
      "commodities": {"val": ["POWER_reactor1_1_50-t", "POWER_reactor2_1_t", "fuel_source_1"]},
      "demand_eq": "3*t",
      "demand_std_dev": "0.0",
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

def test_tech_pref:
    output_file = 'test_tech_pref.sqlite'
    input_file = output_file.replace('.sqlite', '.json')
    with open(input_file, 'w') as f:
        json.dump(input, f)
    s = subprocess.check_output(['cyclus', '-o', output_file, input_file],
                                universal_newlines=True, env=ENV)
    # check if ran successfully and deployed facilities at time step 1 
    cur = functions.get_cursor(output_file)
    agent_entry = cur.execute("select entertime from agententry").fetchall()
    passes = 0 
    for x in range(0,len(agent_entry)): 
        if agent_entry[x][0] == 1: 
            passes = 1 
            break 
    assert(passes == 1)
