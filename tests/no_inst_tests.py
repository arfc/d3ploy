import json
import subprocess
import os

from nose.tools import assert_in

inputfile = {
    "simulation": {
      "archetypes": {
       "spec": [
        {"lib": "d3ploy.demand_fac", "name": "DemandFac"}, 
        {"lib": "agents", "name": "NullRegion"}, 
        {"lib": "d3ploy.no_inst", "name": "NOInst"}
       ]
      }, 
      "control": {"duration": "50", "startmonth": "1", "startyear": "2000"}, 
      "facility": [
       {
        "config": {
         "DemandFac": {
          "demand_commod": "fuel_rx", 
          "demand_rate_max": "2000.", 
          "demand_rate_min": "2000.", 
          "supply_commod": "power_rx", 
          "supply_rate_max": "1000.", 
          "supply_rate_min": "1000."
         }
        }, 
        "name": "Reactor"
       }
      ], 
      "region": {
       "config": {"NullRegion": "\n      "}, 
       "institution": [
        {
         "config": {
          "NOInst": {
           "calc_method": "arma", 
           "demand_commod": "POWER", 
           "demand_std_dev": "1.5", 
           "growth_rate": "0.05", 
           "initial_demand": "100000.0", 
           "prototypes": {"val": "Reactor"}, 
           "steps": "1", 
           "supply_commod": "power_rx",
           "record": 1
          }
         }, 
         "initialfacilitylist": {"entry": {"number": "100", "prototype": "Reactor"}}, 
         "name": "ReactorInst"
        }
       ], 
       "name": "SingleRegion"
      }
     }
    }


def test_demand_calc():
    if os.path.exists('dummy.h5'):
        os.remove('dummy.h5')
    with open('dummy.json', 'w') as f:
        json.dump(inputfile, f)
    env = dict(os.environ)
    env['PYTHONPATH'] = "."
    s = subprocess.check_output(['cyclus', '-o', 'dummy.h5', 'dummy.json'], universal_newlines=True, env=env)
