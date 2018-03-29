import json
import re
import subprocess
import os
import sqlite3 as lite
import copy

from nose.tools import assert_in, assert_true, assert_equals

env = dict(os.environ)
env['PYTHONPATH'] = "."
output_file = 'test_results.sqlite'
input_file = 'test.json'

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

# the template is a dictionary of all simulation parameters
# except the region-institution definition
template = {
 "simulation": {
  "archetypes": {
   "spec": [
    {"lib": "agents", "name": "NullRegion"}, 
    {"lib": "cycamore", "name": "Source"}, 
    {"lib": "cycamore", "name": "Reactor"},
    {"lib": "d3ploy.no_inst", "name": "NOInst"}
   ]
  }, 
  "control": {"duration": "3", "startmonth": "1", "startyear": "2000"}, 
  "recipe": [
   {
    "basis": "mass", 
    "name": "uox", 
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
                         "outrecipe": "fuel",
                         "throughput": "1",
                         "source_record_supply": "fuel"}}, 
   "name": "source"
  },
  {
   "config": {
        "Reactor":{
            "assem_size":"1",
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

""" test1 refers to if NOInst meets the increased demand by deploying more facilities.
    test2 refers to if NOInst meets the decreased demand by decommissioning existing facilities.
"""

""" Test1 Examples"""

init_demand = copy.deepcopy(template)
init_demand["simulation"].update({"region":{
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



def test1_init_demand():
    # tests if NOInst deploys a source given initial demand and no initial facilities

    with open(input_file, 'w') as f:
        json.dump(init_demand, f)
    s = subprocess.check_output(['cyclus', '-o', output_file, input_file],
                                universal_newlines=True, env=env)
    # check if ran successfully
    assert("Cyclus run successful!" in s)

    # getting the sqlite file
    cur = get_cursor(output_file)
    # check if 10 source facilities were deployed by NOInst
    source = cur.execute("SELECT count(*) FROM agententry WHERE Prototype = 'source'"
                         " AND EnterTime = 1").fetchone()
    assert(source[0] == 1)

    cleanup()


init_demand_with_init_facilities = copy.deepcopy(template)
init_demand_with_init_facilities["simulation"].update({"region":{
                         "config": {"NullRegion": "\n      "}, 
                         "institution": {
                          "config": {
                           "NOInst": {
                            "calc_method": "arma", 
                            "demand_commod": "POWER", 
                            "demand_std_dev": "0.0", 
                            "growth_rate": "0.0", 
                            "initial_demand": "2", 
                            "prototypes": {"val": "source"}, 
                            "steps": "1", 
                            "supply_commod": "fuel"
                           }
                          }, 
                          "initialfacilitylist":{
                              "entry":{"number":1,
                                       "prototype":"source"}
                          }, 
                          "name": "source_inst"
                         }, 
                         "name": "SingleRegion"
                         }
                        }
                        )


def test1_init_demand_with_init_facilities():
    # tests if NOInst deploys a source given initial demand and no initial facilities

    with open(input_file, 'w') as f:
        json.dump(init_demand_with_init_facilities, f)
    s = subprocess.check_output(['cyclus', '-o', output_file, input_file],
                                universal_newlines=True, env=env)
    # check if ran successfully
    assert("Cyclus run successful!" in s)

    # getting the sqlite file
    cur = get_cursor(output_file)
    # check if 10 source facilities were deployed by NOInst
    source = cur.execute("SELECT count(*) FROM agententry WHERE Prototype = 'source'"
                         " AND EnterTime = 1").fetchone()
    assert(source[0] == 1)

    cleanup()


increasing_demand = copy.deepcopy(template)
increasing_demand['simulation'].update(
   {"region": {
   "config": {"NullRegion": "\n      "}, 
   "institution": {
    "config": {
     "NOInst": {
      "calc_method": "arma", 
      "demand_commod": "POWER", 
      "demand_std_dev": "0.0", 
      "growth_rate": "1.0", 
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

def test1_increasing_demand():
    # tests if NOInst deploys a source according to increasing demand
    with open(input_file, 'w') as f:
        json.dump(increasing_demand, f)
    s = subprocess.check_output(['cyclus', '-o', output_file, input_file],
                                universal_newlines=True, env=env)
    # check if ran successfully
    assert("Cyclus run successful!" in s)
    # getting the sqlite file
    cur = get_cursor(output_file)
    # check if 1 source facility was deployed by NOInst in timestep 1
    source = cur.execute("SELECT count(*) FROM agententry WHERE Prototype = 'source'"
                         " AND EnterTime = 1").fetchone()
    assert(source[0] == 1)


    # check if 2 source facility was deployed by NOInst in timestep 2
    source = cur.execute("SELECT count(*) FROM agententry WHERE Prototype = 'source'"
                         " AND EnterTime = 2").fetchone()
    assert(source[0] == 2)


    # check if 4 source facility was deployed by NOInst in timestep 3
    source = cur.execute("SELECT count(*) FROM agententry WHERE Prototype = 'source'"
                         " AND EnterTime = 3").fetchone()
    assert(source[0] == 4)

    cleanup()


increasing_demand_with_init_facilities = copy.deepcopy(template)
increasing_demand_with_init_facilities['simulation'].update(
   {  "region": {
   "config": {"NullRegion": "\n      "}, 
   "institution": {
    "config": {
     "NOInst": {
      "calc_method": "arma", 
      "demand_commod": "POWER", 
      "demand_std_dev": "0.0", 
      "growth_rate": "1.0", 
      "initial_demand": "1", 
      "prototypes": {"val": "source"}, 
      "steps": "1", 
      "supply_commod": "fuel"
     }
    }, 
    "initialfacilitylist":{
        "entry":{"number":1,
                 "prototype":"source"}
    }, 
    "name": "source_inst"
   }, 
   "name": "SingleRegion"
  }}
    )


def test1_increasing_demand_with_init_facilities():
    # tests if NOInst deploys a source according to increasing demand
    with open(input_file, 'w') as f:
        json.dump(increasing_demand, f)
    s = subprocess.check_output(['cyclus', '-o', output_file, input_file],
                                universal_newlines=True, env=env)
    # check if ran successfully
    assert("Cyclus run successful!" in s)
    # getting the sqlite file
    cur = get_cursor(output_file)
    # check if 1 source facility was deployed by NOInst in timestep 1
    source = cur.execute("SELECT count(*) FROM agententry WHERE Prototype = 'source'"
                         " AND EnterTime = 1").fetchone()
    print(source[0])
    assert(source[0] == 1)


    # check if 2 source facility was deployed by NOInst in timestep 2
    source = cur.execute("SELECT count(*) FROM agententry WHERE Prototype = 'source'"
                         " AND EnterTime = 2").fetchone()
    print(source[0])
    assert(source[0] == 2)


    # check if 4 source facility was deployed by NOInst in timestep 3
    source = cur.execute("SELECT count(*) FROM agententry WHERE Prototype = 'source'"
                         " AND EnterTime = 3").fetchone()
    print(source[0])
    assert(source[0] == 4)

    cleanup()


reactor_source_no_growth = copy.deepcopy(template)
reactor_source_no_growth['simulation'].update(
   {   "region": {
   "config": {"NullRegion": "\n      "}, 
   "institution": [
    {
     "config": {
      "NOInst": {
       "calc_method": "arma", 
       "demand_commod": "fuel_reactor", 
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
    {
     "config": {
      "NOInst": {
       "calc_method": "arma", 
       "demand_commod": "POWER", 
       "demand_std_dev": "0.0", 
       "growth_rate": "0.0", 
       "initial_demand": "1", 
       "prototypes": {"val": "reactor"}, 
       "steps": "1", 
       "supply_commod": "fuel_reactor"
      }
     },  
     "name": "reactor_inst"
    }
   ], 
   "name": "SingleRegion"
  }}
    )





def test1_reactor_source_no_growth():
    # tests if the reactor and source pair is correctly deployed in static demand
    with open(input_file, 'w') as f:
        json.dump(reactor_source_no_growth, f)
    s = subprocess.check_output(['cyclus', '-o', output_file, input_file],
                                universal_newlines=True, env=env)
    # check if ran successfully
    assert("Cyclus run successful!" in s)

    # getting the sqlite file
    cur = get_cursor(output_file)

    # check if 10 reactor facilities were deployed by NOInst
    reactor = cur.execute("SELECT count(*) FROM agententry WHERE Prototype = 'reactor'"
                         " AND EnterTime = 1").fetchone()
    assert(reactor[0] == 1)

    # check if 10 source facilities were deployed by NOInst
    source = cur.execute("SELECT count(*) FROM agententry WHERE Prototype = 'source'"
                         " AND EnterTime = 1").fetchone()
    assert(source[0] == 1)

    cleanup()

reactor_source_growth = copy.deepcopy(template)
reactor_source_growth['simulation'].update(
   {   "region": {
   "config": {"NullRegion": "\n      "}, 
   "institution": [
    {
     "config": {
      "NOInst": {
       "calc_method": "arma", 
       "demand_commod": "fuel_reactor", 
       "demand_std_dev": "0.0", 
       "growth_rate": "1.0", 
       "initial_demand": "1", 
       "prototypes": {"val": "source"}, 
       "steps": "1", 
       "supply_commod": "fuel"
      }
     }, 
     "name": "source_inst"
    }, 
    {
     "config": {
      "NOInst": {
       "calc_method": "arma", 
       "demand_commod": "POWER", 
       "demand_std_dev": "0.0", 
       "growth_rate": "1.0", 
       "initial_demand": "1", 
       "prototypes": {"val": "reactor"}, 
       "steps": "1", 
       "supply_commod": "fuel_reactor"
      }
     },  
     "name": "reactor_inst"
    }
   ], 
   "name": "SingleRegion"
  }}
    )


def test1_reactor_source_growth():
    # tests if the reactor and source pair is correctly deployed with increase in demand
    with open(input_file, 'w') as f:
        json.dump(reactor_source_growth, f)
    s = subprocess.check_output(['cyclus', '-o', output_file, input_file],
                                universal_newlines=True, env=env)
    # check if ran successfully
    assert("Cyclus run successful!" in s)

    # getting the sqlite file
    cur = get_cursor(output_file)

    # check if 1 reactor facility was deployed by NOInst at timestep 1
    reactor = cur.execute("SELECT count(*) FROM agententry WHERE Prototype = 'reactor'"
                         " AND EnterTime = 1").fetchone()
    assert(reactor[0] == 1)


    # check if 2 reactor facilities were deployed by NOInst in timestep 2
    reactor = cur.execute("SELECT count(*) FROM agententry WHERE Prototype = 'reactor'"
                         " AND EnterTime = 2").fetchone()
    assert(reactor[0] == 2)


    # check if 4 reactor facilities were deployed by NOInst in timestep 3
    reactor = cur.execute("SELECT count(*) FROM agententry WHERE Prototype = 'reactor'"
                         " AND EnterTime = 3").fetchone()
    assert(reactor[0] == 4)

    # check if 1 source facility was deployed by NOInst at timestep 1
    source = cur.execute("SELECT count(*) FROM agententry WHERE Prototype = 'source'"
                         " AND EnterTime = 1").fetchone()
    assert(source[0] == 1)


    # check if 2 source facilities were deployed by NOInst in timestep 2
    source = cur.execute("SELECT count(*) FROM agententry WHERE Prototype = 'source'"
                         " AND EnterTime = 2").fetchone()
    assert(source[0] == 2)


    # check if 4 source facilities were deployed by NOInst in timestep 3
    source = cur.execute("SELECT count(*) FROM agententry WHERE Prototype = 'source'"
                         " AND EnterTime = 3").fetchone()
    assert(source[0] == 4)

    cleanup()



""" Test2 examples"""

phaseout = copy.deepcopy(template)
phaseout["simulation"].update(
                                  {  "region": {
   "config": {"NullRegion": "\n      "}, 
   "institution": {
    "config": {
     "NOInst": {
      "calc_method": "arma", 
      "demand_commod": "POWER", 
      "demand_std_dev": "0.0", 
      "growth_rate": "-1.0", 
      "initial_demand": "1", 
      "prototypes": {"val": "source"}, 
      "steps": "1", 
      "supply_commod": "fuel"
     }
    }, 
    "initialfacilitylist":{
                              "entry":{"number":1,
                                       "prototype":"source"}
    },
    "name": "source_inst"
   }, 
   "name": "SingleRegion"
  }}
  )


def test2_phaseout():
    # tests if NOInst decomissions all deployed facilities with demand going to zero.
    with open(input_file, 'w') as f:
        json.dump(phaseout, f)
    s = subprocess.check_output(['cyclus', '-o', output_file, input_file],
                                universal_newlines=True, env=env)
    # check if ran successfully
    assert("Cyclus run successful!" in s)

    # getting the sqlite file
    cur = get_cursor(output_file)
    # check if 1 source facility has been decommissioned
    source = cur.execute("SELECT count(*) FROM agentexit WHERE ExitTime = 2").fetchone()
    assert(source[0] == 1)

    cleanup()






"""
This is to measure if NOInst behaves correctly with gradual decrease in demand
However we are unsure that NOInst calculates demand by
D = D_0 (1+growth_rate)**(time / seconds_in_a_year)
why is it like this?
What happens when demand/(throughput per facility) is not an integer??


decreasing_demand = {
 "simulation": {
  "archetypes": {
   "spec": [
    {"lib": "agents", "name": "NullRegion"}, 
    {"lib": "cycamore", "name": "Source"}, 
    {"lib": "d3ploy.no_inst", "name": "NOInst"}
   ]
  }, 
  "control": {"duration": "3", "startmonth": "1", "startyear": "2000"}, 
  "facility": {
   "config": {"Source": {"outcommod": "uox", "outrecipe": "uox", "throughput": "1"}}, 
   "name": "source"
  }, 
  "recipe": [
   {
    "basis": "mass", 
    "name": "uox", 
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
     "NOInst": {
      "calc_method": "arma", 
      "demand_commod": "uox", 
      "demand_std_dev": "0.0", 
      "growth_rate": "-0.5", 
      "initial_demand": "10", 
      "prototypes": {"val": "source"}, 
      "steps": "1", 
      "supply_commod": "fuel"
     }
    }, 
    "initialfacilitylist": "\n      ", 
    "name": "source_inst"
   }, 
   "name": "SingleRegion"
  }
 }
}



def test2_decreasing_demand():
    # tests if NOInst deploys a source given initial demand and no initial facilities

    with open(input_file, 'w') as f:
        json.dump(decreasing_demand, f)
    s = subprocess.check_output(['cyclus', '-o', output_file, input_file],
                                universal_newlines=True, env=env)
    # check if ran successfully
    assert("Cyclus run successful!" in s)

    # getting the sqlite file
    cur = get_cursor(output_file)
    # check if 1 source facility has been decommissioned
    source = cur.execute("SELECT count(*) FROM agentexit WHERE ExitTime = 2").fetchone()
    assert(source[0] == 1)

    cleanup()
"""