import json
import subprocess
import os

from nose.tools import assert_in

input= {
    "simulation": {
      "archetypes": {
       "spec": [
        {"lib": "d3ploy.demand_fac", "name": "DemandFac"}, 
        {"lib": "agents", "name": "NullRegion"}, 
        {"lib": "cycamore", "name": "Source"},
        {"lib": "cycamore", "name": "Sink"},
        {"lib": "cycamore", "name": "Enrichment"},
        {"lib": "cycamore", "name": "Reactor"},
        {"lib": "cycamore", "name": "FuelFab"},
        {"lib": "cycamore", "name": "Separations"},
        {"lib": "cycamore", "name": "NOInst"}
       ]
      }, 
      "control": {"duration": "50", "startmonth": "1", "startyear": "2000"}, 
      
      "facility": [
      {
       "config": {
        "Source": {
         "outcommod": "natl_u",
         "outrecipe": "natl_u",
         "throughput": 1e4
        }
       }
       "name": "source"
      }
      ],

      "facility": [
      {
       "config": {
        "Enrichment": {
         "feed_commod": "natl_u",
         "feed_recipe": "natl_u",
         "product_commod": "uox",
         "tails_assay": 0.003,
         "tails_commod": "waste",
         "swu_capacity": 1e4,
         "initial_feed": 1e4
        }
       }
       "name": "enrichment"
      }
      ],

      "facility": [
      {
       "config": {
        "Reactor": {
         "fuel_inrecipes": ["fresh_uox"],
         "fuel_outrecipes": ["spent_uox"],
         "product_commod": "uox",
         "tails_assay": 0.003,
         "tails_commod": "waste",
         "swu_capacity": 1e4,
         "initial_feed": 1e4
        }
       }
       "name": "enrichment"
      }
      ],



      "region": {
       "config": {"NullRegion": "\n      "}, 
       "institution": [
        {
         "config": {
          "NOInst": {
           "calc_method": "arma", 
           "demand_commod": "power", 
           "demand_std_dev": "1.5", 
           "growth_rate": "0.05", 
           "initial_demand": "100000.0", 
           "prototypes": {"val": "Reactor"}, 
           "steps": "1", 
           "supply_commod": "power_rx",
           "record": True
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
    
