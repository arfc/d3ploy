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
# Checking if cyclus simulations and cyclus output files are created and
# populated for each calc method


def test_d3ploy(calc_method):
    test_input = {
        "simulation": {
            "archetypes": {
                "spec": [
                    {"lib": "agents", "name": "NullRegion"},
                    {"lib": "cycamore", "name": "Source"},
                    {"lib": "cycamore", "name": "Reactor"},
                    {"lib": "cycamore", "name": "Sink"},
                    {"lib": "d3ploy.demand_driven_deployment_inst", "name": "DemandDrivenDeploymentInst"}
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
                        "DemandDrivenDeploymentInst": {
                            "calc_method": calc_method,
                            "facility_capacity": {
                                "item": [
                                    {"capacity": "1000", "facility": "reactor"},
                                    {"capacity": "3000", "facility": "source"}
                                ]
                            },
                            "facility_commod": {
                                "item": [
                                    {"commod": "POWER", "facility": "reactor"},
                                    {"commod": "freshfuel", "facility": "source"}
                                ]
                            },
                            "demand_eq": "1000",
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

    name = "test_cont_" + calc_method
    input_file = name + ".json"
    output_file = name + ".sqlite"
    with open(input_file, 'w') as f:
        json.dump(test_input, f)

    try:
        subprocess.check_output(['cyclus', '-o', output_file, input_file],
                                universal_newlines=True, env=ENV)
    except subprocess.CalledProcessError as e:
        print(e.output)
    cur = functions.get_cursor(output_file)
    query = 'SELECT COUNT(*) from agententry WHERE Prototype = "_"'

    for prototype in ['reactor', 'source']:
        row_count = cur.execute(query.replace('_', prototype)).fetchone()[0]
        assert (row_count >= 1)
