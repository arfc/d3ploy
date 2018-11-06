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

INPUT = {
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
      "calc_method": "ma",
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

def test_cont_integ():
    output_file = 'test_cont_int.sqlite'
    input_file = output_file.replace('.sqlite', '.json')
    with open(input_file, 'w') as f:
        json.dump(INPUT, f)
    s = subprocess.check_output(['cyclus', '-o', output_file, input_file],
                                universal_newlines=True, env=ENV)
    # check if ran successfully
    assert("Cyclus run successful!" in s)

    # check if timeseriesdemandfreshfuel, timeseriessupplyfreshfuel, timeseriespower, timeseriessupplypower exist 
    cur = get_cursor('test_cont_int.sqlite')
    fuel_demand = cur.execute("select time, sum(value) from timeseriesdemandfreshfuel group by time").fetchall()
    fuel_supply = cur.execute("select time, sum(value) from timeseriessupplyfreshfuel group by time").fetchall()
    power_demand = cur.execute("select time, sum(value) from timeseriespower group by time").fetchall()
    power_supply = cur.execute("select time, sum(value) from timeseriessupplypower group by time").fetchall()
    total = fuel_demand[0][0]+fuel_supply[0][0]+power_demand[0][0]+power_supply[0][0] 
    assert(total >= 0)
