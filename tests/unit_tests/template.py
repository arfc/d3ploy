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
    {"lib": "cycamore", "name": "Sink"},
    {"lib": "d3ploy.no_inst", "name": "NOInst"}
   ]
  }, 
  "control": {"duration": "15", "startmonth": "1", "startyear": "2000"}, 
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
                         "throughput": "1",
                         "source_record_supply": "fuel"}}, 
   "name": "source"
  },
  {
   "config": {"Sink": {"in_commods": {"val":"spent_uox"},
                       "max_inv_size": 1,
                       "sink_record_demand": "fuel_cap"}}, 
   "name": "sink"
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

""" testA refers to if NOInst meets the increased demand by deploying more facilities.
    testB refers to if NOInst meets the decreased demand by decommissioning existing facilities.
"""

""" TestA Examples"""

""" Test A_1 """
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



def testA1_init_demand():
    # tests if NOInst deploys a source given initial demand and no initial facilities
    output_file = 'init_file.sqlite'
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


""" Test A_2 """
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


def testA2_init_demand_with_init_facilities():
    # tests if NOInst deploys a source given initial demand and no initial facilities
    output_file = 'init_demand_init_fac.sqlite'
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


""" Test A_3 """
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

def testA3_increasing_demand():
    # tests if NOInst deploys a source according to increasing demand
    output_file = 'increasing_demand.sqlite'
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


""" Test A_4 """
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
  }}
    )

def testA4_increasing_demand_with_init_facilities():
    # tests if NOInst deploys a source according to increasing demand
    output_file = 'increasing_demand_with_init_facilites.sqlite'
    with open(input_file, 'w') as f:
        json.dump(increasing_demand_with_init_facilities, f)
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


""" Test A_5 """
reactor_source_init_demand = copy.deepcopy(template)
reactor_source_init_demand['simulation'].update(
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

def testA5_reactor_source_init_demand():
    # tests if the reactor and source pair is correctly deployed in static demand
    output_file = 'reactor_source_init_demand.sqlite'
    with open(input_file, 'w') as f:
        json.dump(reactor_source_init_demand, f)
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




""" Test A_6 """
reactor_source_init_demand_with_init_facilites = copy.deepcopy(template)
reactor_source_init_demand_with_init_facilites['simulation'].update(
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
    {
     "config": {
      "NOInst": {
       "calc_method": "arma", 
       "demand_commod": "power", 
       "demand_std_dev": "0.0", 
       "growth_rate": "0.0", 
       "initial_demand": "2", 
       "prototypes": {"val": "reactor"}, 
       "steps": "1", 
       "supply_commod": "fuel_reactor"
      }
     },  

    "initialfacilitylist":{
        "entry":{"number":1,
                 "prototype":"reactor"}
    },
     "name": "reactor_inst"
    }
   ], 
   "name": "SingleRegion"
  }}
    )

def testA6_reactor_source_init_demand_with_init_facilities():
    # tests if the reactor and source pair is correctly deployed in static demand
    output_file = 'reactor_source_init_demand_with_init_facilities.sqlite'
    with open(input_file, 'w') as f:
        json.dump(reactor_source_init_demand_with_init_facilites, f)
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

    
""" Test A_7 """
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

""" Test A_7 """
def testA7_reactor_source_growth():
    # tests if the reactor and source pair is correctly deployed with increase in demand
    output_file = 'reactor_source_growth.sqlite'
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

"""
source_sink_init_demand = copy.deepcopy(template)
# change in_commod of sink to `fuel`
source_sink_init_demand['simulation']['facility'][1]['config']['Sink']['in_commods']['val'] = 'fuel'
source_sink_init_demand['simulation'].update(
   {   "region": {
   "config": {"NullRegion": "\n      "}, 
   "institution": [
    {
     "config": {
      "NOInst": {
       "calc_method": "arma", 
       "demand_commod": "fuel_cap", 
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
       "supply_commod": "fuel_cap"
      }
     },  
     "name": "sink_inst"
    }
   ], 
   "name": "SingleRegion"
  }}
    )

def testA8_source_sink_init_demand():
    # tests if the reactor and source pair is correctly deployed in static demand
    output_file = 'source_sink_init_demand.sqlite'
    with open(input_file, 'w') as f:
        json.dump(source_sink_init_demand, f)
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


source_sink_init_demand_with_init_facilities = copy.deepcopy(template)
# change in_commod of sink to `fuel`
source_sink_init_demand_with_init_facilities['simulation']['facility'][1]['config']['Sink']['in_commods']['val'] = 'fuel'
source_sink_init_demand_with_init_facilities['simulation'].update(
   {   "region": {
   "config": {"NullRegion": "\n      "}, 
   "institution": [
    {
     "config": {
      "NOInst": {
       "calc_method": "arma", 
       "demand_commod": "fuel_cap", 
       "demand_std_dev": "0.0", 
       "growth_rate": "0.0", 
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
       "supply_commod": "fuel_cap"
      }
     },  
     "initialfacilitylist":{
                              "entry":{"number":1,
                                       "prototype":"sink"}
                          },
     "name": "sink_inst"
    }
   ], 
   "name": "SingleRegion"
  }}
    )

def testA9_source_sink_init_demand_with_init_facilities():
    # tests if the reactor and source pair is correctly deployed in static demand
    output_file = 'source_sink_init_demand_with_init_facilities.sqlite'
    with open(input_file, 'w') as f:
        json.dump(source_sink_init_demand_with_init_facilities, f)
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

"""


""" TestB examples"""

""" Test B_1 """
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


def testB1_phaseout():
    # tests if NOInst decomissions all deployed facilities with demand going to zero.
    output_file = 'phaseout.sqlite'
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



""" Test B_2 """
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



def testB2_decreasing_demand():
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
