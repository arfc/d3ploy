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
hit_list = glob.glob('*.sqlite') + glob.glob('*.json') + glob.glob('*.png') + glob.glob('*.csv') + glob.glob('*.txt')
for file in hit_list:
    os.remove(file)

ENV = dict(os.environ)
ENV['PYTHONPATH'] = ".:" + ENV.get('PYTHONPATH', '')


##### List of types of calc methods that are to be tested #####
calc_methods = ["ma", "arma", "arch", "poly",
                "exp_smoothing", "holt_winters", "fft"]

######################################SCENARIO 7##########################################
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
    {"lib": "d3ploy.timeseries_inst", "name": "TimeSeriesInst"},
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
      "feedbuf_size": "1e6",
      "leftover_commod": "reprocess_waste1",
      "leftoverbuf_size": "1e6",
      "streams": {
       "item": [
        {
         "commod": "separations1Pu",
         "info": {"buf_size": "1e6", "efficiencies": {"item": {"comp": "Pu", "eff": "1"}}}
        },
        {
         "commod": "separations1U",
         "info": {"buf_size": "1e6", "efficiencies": {"item": {"comp": "U", "eff": "1"}}}
        }
       ]
      },
      "throughput": "1e6"
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
         "info": {"buf_size": "1e6", "mixing_ratio": "0.5"}
        },
        {
         "commodities": {
          "item": [
           {"commodity": "separations1U", "pref": "1.0"},
           {"commodity": "separations2U", "pref": "1.0"}
          ]
         },
         "info": {"buf_size": "1e6", "mixing_ratio": "0.5"}
        }
       ]
      },
      "out_buf_size": "1e6",
      "out_commod": "mixeroutput",
      "throughput": "1e6"
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
      "feedbuf_size": "1e6",
      "leftover_commod": "reprocess_waste2",
      "leftoverbuf_size": "1e6",
      "streams": {
       "item": [
        {
         "commod": "separations2Pu",
         "info": {"buf_size": "1e6", "efficiencies": {"item": {"comp": "Pu", "eff": "1"}}}
        },
        {
         "commod": "separations2U",
         "info": {"buf_size": "1e6", "efficiencies": {"item": {"comp": "U", "eff": "1"}}}
        }
       ]
      },
      "throughput": "1e6"
     }
    },
    "name": "separations2"
   },
   {
    "config": {
     "Sink": {
      "in_commods": {"val": ["reprocess_waste1", "reprocess_waste2"]},
      "max_inv_size": "1e6"
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
      "TimeSeriesInst": {
       "calc_method": calc_method,
       "commodities": {
        "val": [
         "POWER_reactor2_3000_2*t_mixeroutput_30000",
         "POWER_reactor1_3000_t",
         "sourceoutput_source_3000"
        ]
       },
       "demand_eq": "1000*t",
       "demand_std_dev": "0.0",
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
       "commodities": {
        "val": [
         "reactor1output_separations1_1e6",
         "separations1Pu_mixer_1e6",
         "reactor2output_separations2_1e6"
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
    all_dict['power'] = tester.supply_demand_dict_driving(
        output_file, demand_eq, 'power')
    all_dict['sourceoutput'] = tester.supply_demand_dict_nondriving(
        output_file, 'sourceoutput',True)
    
    reactor_dict = tester.get_agent_dict(output_file, ['reactor1', 'reactor2'])
    source_dict = tester.get_agent_dict(output_file, ['source'])

    # plots demand, supply, calculated demand, calculated supply for the scenario for each calc method
    plotter.plot_demand_supply_agent(all_dict['power'], reactor_dict, 'power', name, True)
    name2 = "scenario_7_input_"+ calc_method +"_sourceoutput"
    plotter.plot_demand_supply_agent(all_dict['sourceoutput'], source_dict,
                                     'sourceoutput', name2, True)
    
    metric_dict = tester.metrics(all_dict['power'],metric_dict,calc_method,'power',True)
    metric_dict = tester.metrics(all_dict['sourceoutput'],metric_dict,calc_method,'sourceoutput',True)
        
    df = pd.DataFrame(metric_dict)
    df.to_csv('scenario_7_output.csv')
