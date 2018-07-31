"""
This python file contains fleet based unit tests for NO_INST
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

from nose.tools import assert_in, assert_true, assert_equals

# Delete previously generated files
direc = os.listdir('./')
hit_list = glob.glob('*.sqlite') + glob.glob('*.json')
for file in hit_list:
    os.remove(file)

query = 'SELECT count(*) FROM agententry WHERE Prototype = "source"'

ENV = dict(os.environ)
ENV['PYTHONPATH'] = ".:" + ENV.get('PYTHONPATH', '')


def get_cursor(file_name):
    """ Connects and returns a cursor to an sqlite output file

    Parameters
    ----------
    file_name: str
        name of the sqlite file

    Returns
    -------
    sqlite cursor3
    """
    con = lite.connect(file_name)
    con.row_factory = lite.Row
    return con.cursor()


def cleanup():
    """ Removes the generated input file and output sqlite database file."""
    if os.path.exists(output_file):
        os.remove(output_file)
    if os.path.exists(input_file):
        os.remove(input_file)


# the TEMPLATE is a dictionary of all simulation parameters
# except the region-institution definition
TEMPLATE = {
    "simulation": {
        "archetypes": {
            "spec": [
                {"lib": "agents", "name": "NullRegion"},
                {"lib": "cycamore", "name": "Source"},
                {"lib": "cycamore", "name": "Reactor"},
                {"lib": "cycamore", "name": "Sink"},
                {"lib": "d3ploy.no_inst", "name": "NOInst"}
            ]
        },
        "control": {"duration": "120", "startmonth": "1", "startyear": "2000"},
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
        "facility": [{
            "config": {"Source": {"outcommod": "fuel",
                                  "outrecipe": "fresh_uox",
                                  "throughput": "100",
                                  "source_record_supply": "fuel"}},
            "name": "source"
        },
            {
            "config": {"Sink": {"in_commods": {"val": "spent_uox"},
                                "max_inv_size": 1e9,
                                "sink_record_demand": "fuel_cap"}},
            "name": "sink"
        },
            {
            "config": {
                "Reactor": {
                    "assem_size": "100",
                    "cycle_time": "1",
                    "fuel_incommods": {"val": "fuel"},
                    "fuel_inrecipes": {"val": "fresh_uox"},
                    "fuel_outcommods": {"val": "spent_uox"},
                    "fuel_outrecipes": {"val": "spent_uox"},
                    "n_assem_batch": "1",
                    "n_assem_core": "1",
                    "power_cap": "1",
                    "refuel_time": "0",
                    "reactor_fuel_demand": "fuel_reactor"
                }
            },
            "name": "reactor"
        }]
    }
}


""" Test naming convention: 
Test-[alphabet]-[changetype]-[numbering]
alphabet
  - a: only source facility 
  - b: source and reactor facilities 
  - c: source, reactor and sink facilties 
change type 
  - const: constant demand of commodity that drives deployment
  - growth: growing demand of commodity that drives deployment
  - decl: declining demand of commodity that drives deployment
numbering 
  - if test falls under same alphabet and change type category, they
    are numbered 
"""


""" TOLERANCES """
# No. of timesteps accepted for supply to catch up with initial demand
catchup_tolerance = 12 

# No. of facility throughputs for acceptable diff btwn of supply and demand
facility_tolerance = 1


# Test a-const-1 
test_a_const_1_temp = copy.deepcopy(TEMPLATE)
test_a_const_1_temp["simulation"].update({"region": {
    "config": {"NullRegion": "\n      "},
    "institution": {
        "config": {
            "NOInst": {
                "calc_method": "arma",
                "demand_commod": "POWER",
                "demand_std_dev": "0.0",
                "growth_rate": "0.0",
                "initial_demand": "1",
                                  "prototypes": {"val": "source"},
                                  "steps": "1",
                                  "supply_commod": "fuel"
            }
        },
        "name": "source_inst"
    },
    "name": "SingleRegion"
}
}
)


def test_a_const_1():
    output_file = 'test_a_const_1_file.sqlite'
    input_file = output_file.replace('.sqlite', '.json')
    with open(input_file, 'w') as f:
        json.dump(test_a_const_1_temp, f)
    s = subprocess.check_output(['cyclus', '-o', output_file, input_file],
                                universal_newlines=True, env=ENV)
    # check if ran successfully
    assert("Cyclus run successful!" in s)

    # getting the sqlite file
    cur = get_cursor(output_file)

    # check if supply of fuel is within facility_tolerance & catchup_tolerance
