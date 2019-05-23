"""
This algorithm performance test produces plots for basic transition
scenarios that contain source, reactor and sink type facilities.
To use this file, in your command line enter:
python algorithm_performance_tests_transitions.py [transition type]
There are currently 3 transition types in place:
constant, growing and sine.
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
direc = os.listdir("./")
hit_list = (
    glob.glob("*.json")
    + glob.glob("*.png")
    + glob.glob("*.csv")
    + glob.glob("*.txt")
    + glob.glob("*.sqlite")
)
for file in hit_list:
    os.remove(file)

ENV = dict(os.environ)
ENV["PYTHONPATH"] = ".:" + ENV.get("PYTHONPATH", "")

transition_type = str(sys.argv[1])
if transition_type == "constant":
    demand_eq = "10000"
    name = "Constant Transition, Commodity: "
    calc_method = "Constant Transition"
elif transition_type == "growing":
    demand_eq = "10000/(1+np.exp(t-40))+250*t/(1+np.exp(40-t))"
    name = "Growing Transition, Commodity:"
    calc_method = "Growing Transition"
elif transition_type == "sine":
    demand_eq = "(1000*np.sin(np.pi*t/3)+10000)"
    name = "Sinusoidal Transition, Commodity:"
    calc_method = "Sinusoidal Transition"
else:
    raise Exception(
        "The transition type you defined does not exist."
        + " There exists constant, growing and sine transition types. "
    )

output_file = transition_type + "_transition.sqlite"
input_path = os.path.abspath(__file__)
find = "d3ploy/"
indx = input_path.rfind("d3ploy/")
input = input_path.replace(
    input_path[indx + len(find):], "input/%s_transition.xml" % transition_type
)
s = subprocess.check_output(
    ["cyclus", "-o", output_file, input], universal_newlines=True, env=ENV
)

# Initialize dicts
all_dict_power = {}
all_dict_fuel = {}
all_dict_spent_fuel = {}
agent_entry_dict = {}
metric_dict = {}

all_dict_power = tester.supply_demand_dict_driving(
    output_file, demand_eq, "power")
all_dict_fuel = tester.supply_demand_dict_nondriving(output_file, "fuel", True)
all_dict_spent_fuel = tester.supply_demand_dict_nondriving(
    output_file, "spent_fuel", False
)

agent_entry_dict["power"] = tester.get_agent_dict(
    output_file,
    [
        "reactor1",
        "reactor2",
        "reactor3",
        "reactor4",
        "reactor5",
        "reactor6",
        "reactor7",
        "reactor8",
        "reactor9",
        "reactor10",
        "newreactor",
    ],
)
agent_entry_dict["fuel"] = tester.get_agent_dict(
    output_file, ["source", "initialsource"]
)
agent_entry_dict["spent_fuel"] = tester.get_agent_dict(output_file, [
                                                       "lwrsink"])
# plots demand, supply, calculated demand, calculated supply for the
# scenario for each calc method
plotter.plot_demand_supply_agent(
    all_dict_power,
    agent_entry_dict["power"],
    "power",
    name + " Power",
    True,
    False,
    False,
)
plotter.plot_demand_supply_agent(
    all_dict_fuel,
    agent_entry_dict["fuel"],
    "fuel",
    name + " Fuel",
    True,
    False,
    False)
plotter.plot_demand_supply_agent(
    all_dict_spent_fuel,
    agent_entry_dict["spent_fuel"],
    "spent_fuel",
    name + " Spent Fuel",
    False,
    False,
    False,
)

metric_dict = tester.metrics(
    all_dict_power,
    metric_dict,
    calc_method,
    "power",
    True)
metric_dict = tester.metrics(
    all_dict_fuel,
    metric_dict,
    calc_method,
    "fuel",
    True)
metric_dict = tester.metrics(
    all_dict_spent_fuel, metric_dict, calc_method, "spent_fuel", False
)

df = pd.DataFrame(metric_dict)
df.to_csv("scenario.csv")
