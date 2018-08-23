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


# The TEMPLATE is a dictionary of all simulation parameters
# except the region-institution definition which is unique for each test 
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
        "control": {"duration": "1000", "startmonth": "1", "startyear": "2000"},
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
            "config": {"Source": {"outcommod": "fresh_fuel",
                                  "outrecipe": "fresh_uox",
                                  "throughput": "1000"}},
            "name": "source"
        },
            {
            "config": {"Sink": {"in_commods": {"val": "spent_fuel"},
                                "max_inv_size": "1e6"}},
            "name": "sink"
        },
            {
            "config": {
                "Reactor": {
                    "assem_size": "1000",
                    "cycle_time": "18",
                    "fuel_incommods": {"val": "fresh_fuel"},
                    "fuel_inrecipes": {"val": "fresh_uox"},
                    "fuel_outcommods": {"val": "spent_fuel"},
                    "fuel_outrecipes": {"val": "spent_uox"},
                    "n_assem_batch": "1",
                    "n_assem_core": "3",
                    "power_cap": "1000",
                    "refuel_time": "1",
                    "reactor_fuel_demand": "fuel_reactor"
                }
            },
            "name": "reactor"
        }]
    }
}


""" 
Test naming convention

Test-[Alphabet]-[Demand]-[Numbering]
[Alphabet]
  - [A]: facility - source, demand-driving commodity - fresh fuel 
  - [B]: facility - source and reactor, demand-driving commodity - power
  - [C]: facility - source, reactor and sink , demand-driving commodity - power
Demand
  - [Constant]: constant demand of commodity that drives deployment
  - [Growth]: growing demand of commodity that drives deployment
  - [Decline]: declining demand of commodity that drives deployment
Numbering
  - If test falls under same Alphabet and Demand category, they 
    are numbered 
"""


""" TOLERANCES """
# No. of timesteps accepted for supply to catch up with initial demand
catchup_tolerance = 12 

# Acceptable percentage difference diff btwn supply and demand
facility_tolerance = 10 #[%]


def demand_curve(initial_demand,growth_rate,time_point):
    """ Uses initial demand, growth rate and list of timesteps to 
    output the corresponding demand curve points 

    Parameters
    ----------
    initial_demand : int, initial demand of demand-driving commodity 
    growth_rate : int, growth rate of demand-driving commodity 
    time_point: int, a time step in the simulation  

    Returns
    -------
    demand_values : int, demand point corresponding to time_point  
    """
    demand_point = initial_demand*(1+growth_rate)**(time_point/12)
    return demand_point

#######################TEST_A_Constant_1####################################
""" 
Test A-Constant-1 
        - A: facility - source, demand-driving commodity - fresh fuel 
        - Constant: constant demand of fuel commodity that drives deployment 
        - 1: first test of A-Constant type 
"""
# Configuring the simulation template for this test instance 
test_a_const_1_template = copy.deepcopy(TEMPLATE)
test_a_const_1_template["simulation"].update({"region": {
    "config": {"NullRegion": "\n      "},
    "institution": {
        "config": {
            "NOInst": {
                "calc_method": "arma", 
                "commodities": {"val": ["fuel"]}, 
                "demand_std_dev": "0.0", 
                "growth_rate": "1.0", 
                "initial_demand": "1000", 
                "record": "1", 
                "steps": "1"
            }
        },
        "name": "source_inst"
    },
    "name": "SingleRegion"
}
}
)

# actual test part
def test_a_const_1():
    output_file = 'test_a_const_1_file.sqlite'
    input_file = output_file.replace('.sqlite', '.json')
    with open(input_file, 'w') as f:
        json.dump(test_a_const_1_template, f)
    s = subprocess.check_output(['cyclus', '-o', output_file, input_file],
                                universal_newlines=True, env=ENV)
    # check if ran successfully
    assert("Cyclus run successful!" in s)

    # getting the sqlite file
    cur = get_cursor('test_a_const_1_file.sqlite')

    # check if supply of fuel is within facility_tolerance & catchup_tolerance
    fuel_supply = cur.execute("select time, sum(value) from timeseriessupplyfuel group by time").fetchall()
    num = 0
    for pt in range(catchup_tolerance,len(fuel_supply)):
        fuel_supply_point = fuel_supply[pt][1]
        time_point = fuel_supply[pt][0]
        # if supply curve value is larger/smaller than demand curve by facility_tolerance 
        # at any timestep (larger than catch up tolerance) the num counter will be larger 
        # than 1 and the test will fail
        if ((fuel_supply_point-demand_curve(1000,0,time_point))>(facility_tolerance*100)):
            num = num + 1
        else: 
            num = num+0 

    assert(num == 0)

##############################################################################


############################TEST_A_Grow_1#####################################
""" Test a-grow-1 
        - a: only source facility 
        - grow: growing demand of fuel commodity that drives deployment 
        - 1: first test of a-const type 
"""
# Configuring it for this test instance 
test_a_grow_1_temp = copy.deepcopy(TEMPLATE)
test_a_grow_1_temp["simulation"].update({"region": {
    "config": {"NullRegion": "\n      "},
    "institution": {
        "config": {
            "NOInst": {
                "calc_method": "arma", 
                "commodities": {"val": ["fuel"]}, 
                "demand_std_dev": "0.0", 
                "growth_rate": "1.0", 
                "initial_demand": "1000", 
                "record": "1", 
                "steps": "1"
            }
        },
        "name": "source_inst"
    },
    "name": "SingleRegion"
}
}
)

# actual test part
def test_a_grow_1():
    output_file = 'test_a_grow_1_file.sqlite'
    input_file = output_file.replace('.sqlite', '.json')
    with open(input_file, 'w') as f:
        json.dump(test_a_grow_1_template, f)
    s = subprocess.check_output(['cyclus', '-o', output_file, input_file],
                                universal_newlines=True, env=ENV)
    # check if ran successfully
    assert("Cyclus run successful!" in s)

    # getting the sqlite file
    cur = get_cursor('test_a_grow_1_file.sqlite')

    # check if supply of fuel is within facility_tolerance & catchup_tolerance
    fuel_supply = cur.execute("select time, sum(value) from timeseriessupplyfuel group by time").fetchall()
    
    num = 0
    for pt in range(catchup_tolerance,len(fuel_supply)):
        fuel_supply_point = fuel_supply[pt][1]
        time_point = fuel_supply[pt][0]
        # if supply curve value is larger/smaller than demand curve by facility_tolerance 
        # at any timestep (larger than catch up tolerance) the num counter will be larger 
        # than 1 and the test will fail
        if ((fuel_supply_point-demand_curve(1000,1,time_point))>(facility_tolerance*100)):
            num = num + 1
        else: 
            num = num+0 

    assert(num == 0)

######################################################################################

#################################TEST_A_Grow_2########################################
    """ Test a-grow-2 
        - a: only source facility 
        - grow: growing demand of fuel commodity that drives deployment 
        - 2: 2nd test of a-const type (it has no initial demand)
"""
# Configuring it for this test instance 
test_a_grow_2_temp = copy.deepcopy(TEMPLATE)
test_a_grow_2_temp["simulation"].update({"region": {
    "config": {"NullRegion": "\n      "},
    "institution": {
        "config": {
            "NOInst": {
                "calc_method": "arma", 
                "commodities": {"val": ["fuel"]}, 
                "demand_std_dev": "0.0", 
                "growth_rate": "1.0", 
                "initial_demand": "0", 
                "record": "1", 
                "steps": "1"
            }
        },
        "name": "source_inst"
    },
    "name": "SingleRegion"
}
}
)

# actual test part
def test_a_grow_2():
    output_file = 'test_a_grow_1_file.sqlite'
    input_file = output_file.replace('.sqlite', '.json')
    with open(input_file, 'w') as f:
        json.dump(test_a_grow_2_template, f)
    s = subprocess.check_output(['cyclus', '-o', output_file, input_file],
                                universal_newlines=True, env=ENV)
    # check if ran successfully
    assert("Cyclus run successful!" in s)

    # getting the sqlite file
    cur = get_cursor('test_a_grow_2_file.sqlite')

    # check if supply of fuel is within facility_tolerance & catchup_tolerance
    fuel_supply = cur.execute("select time, sum(value) from timeseriessupplyfuel group by time").fetchall()
    
    num = 0
    for pt in range(catchup_tolerance,len(fuel_supply)):
        fuel_supply_point = fuel_supply[pt][1]
        time_point = fuel_supply[pt][0]
        # if supply curve value is larger/smaller than demand curve by facility_tolerance 
        # at any timestep (larger than catch up tolerance) the num counter will be larger 
        # than 1 and the test will fail
        if ((fuel_supply_point-demand_curve(0,1,time_point))>(facility_tolerance*100)):
            num = num + 1
        else: 
            num = num+0 

    assert(num == 0)

#######################################################################################    