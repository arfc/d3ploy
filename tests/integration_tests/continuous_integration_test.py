import json
import re
import subprocess
import os
import sqlite3 as lite
import pytest
import copy
import glob
import sys
import d3ploy.tester as functions
from nose.tools import assert_in, assert_true, assert_equals

# Delete previously generated files
direc = os.listdir('./')
hit_list = glob.glob('*.sqlite') + glob.glob('*.json')
for file in hit_list:
    os.remove(file)

ENV = dict(os.environ)
ENV['PYTHONPATH'] = ".:" + ENV.get('PYTHONPATH', '')

#######################################################
# Checking if cyclus simulations and cyclus output files are created and populated for each calc method

calc_methods = ["ma", "arma", "arch", "poly",
                "exp_smoothing", "holt_winters", "fft"]

test_cont_input = {}

for x in range(0, len(calc_methods)):
    test_cont_input[x] = {
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
            "control": {"duration": "10", "startmonth": "1", "startyear": "2000"},
            "facility": [
                {
                    "config": {
                        "Source": {"outcommod": "freshfuel", "outrecipe": "fresh_uox", "throughput": "3000"}
                    },
                    "name": "source"
                },
                {
                    "config": {"Sink": {"in_commods": {"val": "spent_fuel"}, "max_inv_size": "1e6"}},
                    "name": "sink"
                },
                {
                    "config": {
                        "Reactor": {
                            "assem_size": "1000",
                            "cycle_time": "18",
                            "fuel_incommods": {"val": "freshfuel"},
                            "fuel_inrecipes": {"val": "fresh_uox"},
                            "fuel_outcommods": {"val": "spent_fuel"},
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
            ],
            "region": {
                "config": {"NullRegion": "\n      "},
                "institution": {
                    "config": {
                        "TimeSeriesInst": {
                            "calc_method": calc_methods[x],
                            "commodities": {"val": ["POWER_reactor_1000", "freshfuel_source_3000"]},
                            "demand_eq": "1000",
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

total = {}

for x in range(0, len(calc_methods)):
    name = "test_cont_"+calc_methods[x]
    input_file = name+".json"
    output_file = name+".sqlite"
    with open(input_file, 'w') as f:
        json.dump(test_cont_input[x], f)
    s = subprocess.check_output(['cyclus', '-o', output_file, input_file],
                                universal_newlines=True, env=ENV)

    cur = functions.get_cursor(output_file)
    fuel_demand = cur.execute(
        "select time, sum(value) from timeseriesdemandfreshfuel group by time").fetchall()
    fuel_supply = cur.execute(
        "select time, sum(value) from timeseriessupplyfreshfuel group by time").fetchall()
    power_demand = cur.execute(
        "select time, sum(value) from timeseriespower group by time").fetchall()
    power_supply = cur.execute(
        "select time, sum(value) from timeseriessupplypower group by time").fetchall()
    # Adding up the first time step of each table
    total[calc_methods[x]] = fuel_demand[0][0] + \
        fuel_supply[0][0]+power_demand[0][0]+power_supply[0][0]


# checking if the first time step for each table occured
def test_cont_integ_ma():
    assert(total['ma'] == 4)


def test_cont_integ_arma():
    assert(total['arma'] == 4)


def test_cont_integ_arch():
    assert(total['arch'] == 4)


def test_cont_integ_poly():
    assert(total['poly'] == 4)


def test_cont_integ_exp_smoothing():
    assert(total['exp_smoothing'] == 4)


def test_cont_integ_holt_winters():
    assert(total['holt_winters'] == 4)


def test_cont_integ_fft():
    assert(total['fft'] >= 4)
