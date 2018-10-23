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
from matplotlib import pyplot as plt
import numpy as np

from nose.tools import assert_in, assert_true, assert_equals

# Delete previously generated files
direc = os.listdir('./')
hit_list = glob.glob('*.sqlite') + glob.glob('*.json') + glob.glob('*.png')
for file in hit_list:
    os.remove(file)

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
        "control": {"duration": "100", "startmonth": "1", "startyear": "2000"},
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
                                  "throughput": "3000"}},
            "name": "source"
        },
            {
            "config": {"Sink": {"in_commods": {"val": "fuel"},
                                "max_inv_size": "1e6"}},
            "name": "sink"
        },
        {
            "config": {
                "Reactor": {
                    "assem_size": "1000",
                    "cycle_time": "1",
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
facility_tolerance = 20 #[%]

# Acceptable number of facility tolerance 
no_fac = 1 

# fuel facility throughput 
thru = 3000

def demand_curve(type,time_point):
    """ Uses initial demand, growth rate and list of timesteps to 
    output the corresponding demand curve points 

    Parameters
    ----------
    time_point: int, a time step in the simulation  

    Returns
    -------
    demand_values : int, demand point corresponding to time_point  
    """
    if type == 'a-const-1':
        demand_point = 10000
    elif type == 'a-grow-1':
        demand_point = 100*time_point
    elif type == 'a-grow-2':
        demand_point = 10*(1+1.5)**(time_point/12)
    return demand_point

# For testing if supply is within a facility tolerance of demand 
def supply_within_demand_fac_tol(sql_file,type):
    # getting the sqlite file
    cur = get_cursor(sql_file)

    # check if supply of fuel is within facility_tolerance & catchup_tolerance
    fuel_supply = cur.execute("select time, sum(value) from timeseriessupplyfuel group by time").fetchall()
    num = 0
    for pt in range(0,len(fuel_supply)):
        fuel_supply_point = fuel_supply[pt][1]
        time_point = fuel_supply[pt][0]
        # if supply curve value is larger/smaller than demand curve by no_fac amount
        # at any timestep the num counter will be larger 
        # than 1 and the test will fail
        fuel_demand_point = demand_curve(type,time_point)
        diff = fuel_supply_point - fuel_demand_point
        if diff>no_fac*thru:
            num = num + 1
        else: 
            num = num+0 
    return num

# For testing if supply is in a percentage tolerance of demand
def supply_within_demand_range(sql_file,type):  
    # getting the sqlite file
    cur = get_cursor(sql_file)

    # check if supply of fuel is within facility_tolerance & catchup_tolerance
    fuel_supply = cur.execute("select time, sum(value) from timeseriessupplyfuel group by time").fetchall()
    num = 0
    for pt in range(catchup_tolerance,len(fuel_supply)):
        fuel_supply_point = fuel_supply[pt][1]
        time_point = fuel_supply[pt][0]
        # if supply curve value is larger/smaller than demand curve by facility_tolerance percentage
        # at any timestep (larger than catch up tolerance) the num counter will be larger 
        # than 1 and the test will fail
        fuel_demand_point = demand_curve(type,time_point)
        percentage_diff = abs((fuel_supply_point - fuel_demand_point)/fuel_demand_point)*100
        if percentage_diff>facility_tolerance:
            num = num + 1
        else: 
            num = num+0 
    return num

def plot_demand_supply(sqlite,demand,test):
    cur = get_cursor(sqlite)
    fuel_supply = cur.execute("select time, sum(value) from timeseriessupplyfuel group by time").fetchall()
    calc_fuel_demand = cur.execute("select time, sum(value) from timeseriesfuelcalc_demand group by time").fetchall()
    calc_fuel_supply = cur.execute("select time, sum(value) from timeseriesfuelcalc_supply group by time").fetchall()
    dict_supply = {}
    dict_calc_demand = {}
    dict_calc_supply = {}
    for x in range(0,len(fuel_supply)):
        dict_supply[fuel_supply[x][0]] = fuel_supply[x][1]
        dict_calc_demand[fuel_supply[x][0]] = calc_fuel_demand[x][1]
        dict_calc_supply[fuel_supply[x][0]] = calc_fuel_supply[x][1]
    t = np.fromiter(dict_supply.keys(),dtype=float)
    fuel_demand = eval(demand)
    if isinstance(fuel_demand,int):
        fuel_demand = fuel_demand*np.ones(len(t))

    fig, ax = plt.subplots(figsize=(15, 7))
    ax.plot(t,fuel_demand,'*',label='Demand')
    ax.plot(*zip(*sorted(dict_supply.items())),'*',label = 'Supply')
    ax.plot(*zip(*sorted(dict_calc_demand.items())),'o',alpha = 0.5,label = 'Calculated Demand')
    ax.plot(*zip(*sorted(dict_calc_supply.items())),'o',alpha = 0.5,label = 'Calculated Supply')
    ax.grid()
    ax.set_xlabel('Time (month timestep)', fontsize=14)
    ax.set_ylabel('Mass (kg)' , fontsize=14)
    handles, labels = ax.get_legend_handles_labels()
    ax.legend(
            handles,
            labels,
            fontsize=11,
            loc='upper center',
            bbox_to_anchor=(
                1.1,
                1.0),
            fancybox=True)
    ax.set_title('Fuel Demand Supply plot')
    plt.savefig(test, dpi=300,bbox_inches='tight')

#######################TEST_A_Constant_1####################################
""" 
Test A-Constant-1 
        - [A]: facility - source, demand-driving commodity - fresh fuel 
        - [Constant]: constant demand of fuel commodity that drives deployment 
        - [1]: first test of A-Constant type 
"""
# Configuring the simulation template for this test instance 
test_a_const_1_template = copy.deepcopy(TEMPLATE)
test_a_const_1_template["simulation"].update({"region": {
    "config": {"NullRegion": "\n      "},
    "institution": {
        "config": {
            "NOInst": {
                "calc_method": "arma",
                "commodities": {"val": ["fuel_source_3000"]},
                "driving_commod": "fuel",
                "demand_std_dev": "1.0",
                "demand_eq": "10000",
                "record": "1",
                "steps": "1"
            }
        },
        "name": "source_inst"
    },
    "name": "SingleRegion"
}})

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

    # plot 
    plot_demand_supply('test_a_const_1_file.sqlite','10000','a-const-1')

    # check if supply of fuel is within facility_tolerance & catchup_tolerance
    number_within_tolerance = supply_within_demand_fac_tol('test_a_const_1_file.sqlite','a-const-1')
    assert(number_within_tolerance == 0)

##############################################################################

############################TEST_A_Grow_1#####################################
""" Test a-growth-1 
        - [A]: facility - source, demand-driving commodity - fresh fuel 
        - [Growth]: growing demand of commodity that drives deployment
        - [1]: first test of a-growth type 
"""
# Configuring it for this test instance 
test_a_grow_1_temp = copy.deepcopy(TEMPLATE)
test_a_grow_1_temp["simulation"].update({"region": {
    "config": {"NullRegion": "\n      "},
    "institution": {
        "config": {
            "NOInst": {
                "calc_method": "arma", 
                "commodities": {"val": ["fuel_source_3000"]}, 
                "driving_commod": "fuel",
                "demand_std_dev": "1.0", 
                "demand_eq": "100*t", 
                "record": "1", 
                "steps": "1"
            }
        },
        "name": "source_inst"
    },
    "name": "SingleRegion"
}})

# actual test part
def test_a_grow_1():
    output_file = 'test_a_grow_1_file.sqlite'
    input_file = output_file.replace('.sqlite', '.json')
    with open(input_file, 'w') as f:
        json.dump(test_a_grow_1_temp, f)
    s = subprocess.check_output(['cyclus', '-o', output_file, input_file],
                                universal_newlines=True, env=ENV)
    # check if ran successfully
    assert("Cyclus run successful!" in s)

    # plot 
    plot_demand_supply('test_a_grow_1_file.sqlite','100*t','a-grow-1')

    # check if supply of fuel is within facility_tolerance & catchup_tolerance
    number_within_tolerance = supply_within_demand_fac_tol('test_a_grow_1_file.sqlite','a-grow-1')
    assert(number_within_tolerance == 0)

######################################################################################

#################################TEST_A_Grow_2########################################
""" Test a-grow-2 
    - [A]: facility - source, demand-driving commodity - fresh fuel 
    - [Growth]: growing demand of commodity that drives deployment
    - [2]: second test of a-growth type 
"""
# Configuring it for this test instance 
test_a_grow_2_temp = copy.deepcopy(TEMPLATE)
test_a_grow_2_temp["simulation"].update({"region": {
    "config": {"NullRegion": "\n      "},
    "institution": {
        "config": {
            "NOInst": {
                "calc_method": "ma",
                "commodities": {"val": ["fuel_source_3000"]},
                "driving_commod": "fuel",
                "demand_std_dev": "1.0",
                "demand_eq": "10*(1+1.5)**(t/12)",
                "record": "1",
                "steps": "1"
            }
        },
        "name": "source_inst"
    },
    "name": "SingleRegion"
}})

# actual test part
def test_a_grow_2():
    output_file = 'test_a_grow_2_file.sqlite'
    input_file = output_file.replace('.sqlite', '.json')
    with open(input_file, 'w') as f:
        json.dump(test_a_grow_2_temp, f)
    s = subprocess.check_output(['cyclus', '-o', output_file, input_file],
                                universal_newlines=True, env=ENV)
    # check if ran successfully
    assert("Cyclus run successful!" in s)

    # plot 
    plot_demand_supply('test_a_grow_2_file.sqlite','10*(1+1.5)**(t/12)','a-grow-2')

    # check if supply of fuel is within facility_tolerance & catchup_tolerance
    number_within_tolerance = supply_within_demand_fac_tol('test_a_grow_2_file.sqlite','a-grow-2')
    assert(number_within_tolerance == 0)

#######################################################################################             
