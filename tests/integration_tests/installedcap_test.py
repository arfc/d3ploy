""" This python file contains installed capacity tests
for DemandDrivenDeploymentInst and SupplyDrivenDeploymentInst
archetypes.
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

scenario_template = {
    "simulation": {
        "archetypes": {
            "spec": [
                    {"lib": "agents", "name": "NullRegion"},
                    {"lib": "cycamore", "name": "Source"},
                    {"lib": "cycamore", "name": "Reactor"},
                    {"lib": "cycamore", "name": "Sink"},
                    {"lib": "cycamore", "name": "Storage"},
                    {"lib": "d3ploy.demand_driven_deployment_inst", "name": "DemandDrivenDeploymentInst"},
                    {"lib": "d3ploy.supply_driven_deployment_inst", "name": "SupplyDrivenDeploymentInst"}
            ]
        },
        "control": {"duration": "10", "startmonth": "1", "startyear": "2000"},
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
        ]}}

######################## Test Installed Cap ##############################
demand_eq = "1000"
scenario_input = copy.deepcopy(scenario_template)
scenario_input["simulation"].update({"facility": [{
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
            "cycle_time": "3",
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
}]})
scenario_input["simulation"].update({"region": {"config": {"NullRegion": "\n      "},
                                                "institution": [
    {
        "config": {
            "DemandDrivenDeploymentInst": {
                "calc_method": "ma",
                "demand_eq": demand_eq,
                "driving_commod": "POWER",
                "facility_capacity": {"item": {"capacity": "3000", "facility": "source"}},
                "facility_commod": {"item": {"commod": "fuel", "facility": "source"}},
                "installed_cap": "1",
                "record": "0",
                "steps": "1"
            }
        },
        "name": "non_driving_inst"
    },
    {
        "config": {
            "DemandDrivenDeploymentInst": {
                "calc_method": "ma",
                "demand_eq": demand_eq,
                "driving_commod": "POWER",
                "facility_capacity": {"item": {"capacity": "1000", "facility": "reactor"}},
                "facility_commod": {"item": {"commod": "POWER", "facility": "reactor"}},
                "installed_cap": "1",
                "record": "0",
                "steps": "1"
            }
        },
        "name": "driving_inst"
    }
],
    "name": "SingleRegion"

}})


def test_installed_cap():
    """This test will pass if only one reactor agent enter the simulation
    because the deployment of facilities is based on installed capacity"""

    name = "scenario_input_"
    input_file = name + ".json"
    output_file = name + ".sqlite"
    with open(input_file, 'w') as f:
        json.dump(scenario_input, f)

    s = subprocess.check_output(['cyclus', '-o', output_file, input_file],
                                universal_newlines=True,)
    cursor = functions.get_cursor(output_file)
    agententry = cursor.execute('SELECT entertime FROM agententry WHERE ' +
                                'prototype == "reactor"').fetchall()
    assert (len(agententry) == 1)


###################### TEST initial facility list ######################
demand_eq = "1000"
scenario_input2 = copy.deepcopy(scenario_template)
scenario_input2["simulation"].update({"facility": [{
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
            "cycle_time": "3",
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
}]})
scenario_input2["simulation"].update({"region": {"config": {"NullRegion": "\n      "},
                                                 "institution": [
    {
        "config": {
            "DemandDrivenDeploymentInst": {
                "calc_method": "ma",
                "demand_eq": demand_eq,
                "driving_commod": "POWER",
                "facility_capacity": {"item": {"capacity": "3000", "facility": "source"}},
                "facility_commod": {"item": {"commod": "fuel", "facility": "source"}},
                "installed_cap": "1",
                "record": "0",
                "steps": "1"
            }
        },
        "name": "non_driving_inst"
    },
    {
        "config": {
            "DemandDrivenDeploymentInst": {
                "calc_method": "ma",
                "demand_eq": demand_eq,
                "driving_commod": "POWER",
                "facility_capacity": {"item": {"capacity": "1000", "facility": "reactor"}},
                "facility_commod": {"item": {"commod": "POWER", "facility": "reactor"}},
                "installed_cap": "1",
                "record": "0",
                "steps": "1"
            }
        },
        "initialfacilitylist": {"entry": {"number": "1", "prototype": "reactor"}},
        "name": "driving_inst"
    }
],
    "name": "SingleRegion"

}})


def test_initial_facility():
    """This test will pass if only 1 reactor agent enter the simulation
    , 1 reactor is added using the initial facility list. So if the deployment
    of facilities is based on installed capacity, no other facilities will be
    deployed """

    name = "scenario_input2_"
    input_file = name + ".json"
    output_file = name + ".sqlite"
    with open(input_file, 'w') as f:
        json.dump(scenario_input2, f)

    s = subprocess.check_output(['cyclus', '-o', output_file, input_file],
                                universal_newlines=True,)
    cursor = functions.get_cursor(output_file)
    agententry = cursor.execute('SELECT entertime FROM agententry WHERE ' +
                                'prototype == "reactor"').fetchall()
    assert (len(agententry) == 1)


############################ TEST SUPPLY DRIVEN ##########################
def test_backdeployment_IC():
    """This test will pass if only 1 sink agent enters the simulation
    , 1 sink is added using the initial facility list. So if the deployment
    of facilities is based on installed capacity, no other facilities will be
    deployed """
    output_ = 'test_supplydriven_installedcap.sqlite'
    input_path = os.path.abspath(__file__)
    find = 'd3ploy/'
    indx = input_path.rfind('d3ploy/')
    input_ = input_path.replace(
        input_path[indx + len(find):], 'input/linear_pow_demand_backdeployment_initialfac.xml')
    s = subprocess.check_output(['cyclus', '-o', output_, input_],
                                universal_newlines=True, env=ENV)
    cur = functions.get_cursor(output_)
    reactor2_entry = cur.execute('SELECT Prototype FROM agententry WHERE ' +
                                 'prototype == "sink"').fetchall()
    assert (len(reactor2_entry) == 1)
