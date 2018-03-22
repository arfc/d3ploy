import json
import subprocess
import os
import nose

#from nose.tools import assert

def test_arma():
    cleaning()
    env = dict(os.environ)
    env['PYTHONPATH'] = "."
    s = subprocess.check_output(['cyclus', '-o', 'dummy.h5', 'test.json'], universal_newlines=True, env=env)
    # Testing Building Reactors    
    with open('POWER.txt') as f:
        rx_hist = f.readlines()
    reactors, power = read_info(rx_hist)
    assert reactors > 0
    assert power < 0
    # Testing building mines
    with open('uranium.txt') as f:
        mine_hist = f.readlines()
    mine, uranium = read_info(mine_hist)
    assert mine > 0
    assert uranium < 0
    cleaning()

def cleaning():
    if os.path.exists('dummy.h5'):
        os.remove('dummy.h5')
    if os.path.exists('POWER.txt'):
        os.remove('POWER.txt')
    if os.path.exists('uranium.txt'):
        os.remove('uranium.txt')
    
def read_info(text):
    diff = []
    #check to see if facilities are deployed
    first = float(text[0].split()[3])
    last = float(text[-1].split()[3])
    built = last > first
    #check to make sure overprediction occurs
    for line in text:
        vals = line.split()
        diff.append((float(vals[7])-float(vals[5]))/float(vals[7]))
    avg = sum(diff)/len(diff)
    return built, avg

'''
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
      "region": [{
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
    }]
  }
}
'''
