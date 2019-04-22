""" This python file contains tech pref capability tests for TimeSeriesInst
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


TEMPLATE = {
    "simulation": {
        "archetypes": {
            "spec": [
                {"lib": "agents", "name": "NullRegion"},
                {"lib": "cycamore", "name": "Source"},
                {"lib": "cycamore", "name": "Reactor"},
                {"lib": "cycamore", "name": "Sink"},
                {"lib": "d3ploy.demand_driven_deployment_inst",
                 "name": "DemandDrivenDeploymentInst"}
            ]
        },
        "control": {"duration": "10", "startmonth": "1", "startyear": "2000"},
        "facility": [
            {
                "config": {"Source": {"outcommod": "fuel",
                                      "outrecipe": "fresh_uox",
                                                   "throughput": "1"}},
                "name": "source"
            },
            {
                "config": {"Sink": {"in_commods": {"val": "spent_uox"},
                                    "max_inv_size": "10"}},
                "name": "sink"
            },
            {
                "config": {
                    "Reactor": {
                        "assem_size": "1",
                        "cycle_time": "1",
                        "fuel_incommods": {"val": "fuel"},
                        "fuel_inrecipes": {"val": "fresh_uox"},
                        "fuel_outcommods": {"val": "spent_uox"},
                        "fuel_outrecipes": {"val": "spent_uox"},
                        "n_assem_batch": "1",
                        "n_assem_core": "1",
                        "power_cap": "1",
                        "refuel_time": "0"
                    }
                },
                "name": "reactor1"
            },
            {
                "config": {
                    "Reactor": {
                        "assem_size": "1",
                        "cycle_time": "1",
                        "fuel_incommods": {"val": "fuel"},
                        "fuel_inrecipes": {"val": "fresh_uox"},
                        "fuel_outcommods": {"val": "spent_uox"},
                        "fuel_outrecipes": {"val": "spent_uox"},
                        "n_assem_batch": "1",
                        "n_assem_core": "1",
                        "power_cap": "1",
                        "refuel_time": "0"
                    }
                },
                "name": "reactor2"
            }
        ],
        "recipe": [
            {
                "basis": "mass",
                "name": "fresh_uox",
                "nuclide": [{"comp": "0.711", "id": "U235"},
                            {"comp": "99.289", "id": "U238"}]
            },
            {
                "basis": "mass",
                "name": "spent_uox",
                "nuclide": [{"comp": "50", "id": "Kr85"},
                            {"comp": "50", "id": "Cs137"}]
            }
        ]
    }
}

# ----------------------------------------------------------------------------- #
# This test will fail if the inclusion of a 20% supply buffer doesn't result in 
# the calculated demand being 20% larger than a simulation without the supply
# buffer. 

nobuf_template = copy.deepcopy(TEMPLATE)
nobuf_template["simulation"].update({"region": {
    "config": {"NullRegion": "\n      "},
    "institution": {
        "config": {
            "DemandDrivenDeploymentInst": {
                "calc_method": "poly",
                "facility_capacity": {
                    "item": [
                        {"capacity": "1", "facility": "reactor1"},
                        {"capacity": "1", "facility": "source"}
                    ]
                },
                "facility_commod": {
                    "item": [
                        {"commod": "POWER", "facility": "reactor1"},
                        {"commod": "fuel", "facility": "source"}
                    ]
                },
                "demand_eq": "3*t",
                "record": "1",
                "steps": "1"
            }
        },
        "name": "source_inst"
    },
    "name": "SingleRegion"
}
})


yesbuf_template = copy.deepcopy(TEMPLATE)
yesbuf_template["simulation"].update({"region": {
    "config": {"NullRegion": "\n      "},
    "institution": {
        "config": {
            "DemandDrivenDeploymentInst": {
                "calc_method": "poly",
                "facility_capacity": {
                    "item": [
                        {"capacity": "1", "facility": "reactor1"},
                        {"capacity": "1", "facility": "source"}
                    ]
                },
                "facility_commod": {
                    "item": [
                        {"commod": "POWER", "facility": "reactor1"},
                        {"commod": "fuel", "facility": "source"}
                    ]
                },
                "supply_buffer": {
                    "item": [
                        {"commod": "POWER","buffer": "0.2"}
                    ]
                },
                "demand_eq": "3*t",
                "record": "1",
                "steps": "1"
            }
        },
        "name": "source_inst"
    },
    "name": "SingleRegion"
}
})

def test_supply_buffer():
    output_file_nobuf = 'nobuf.sqlite'
    output_file_yesbuf = 'yesbuf.sqlite'
    input_file_nobuf = output_file_nobuf.replace('.sqlite', '.json')
    input_file_yesbuf = output_file_yesbuf.replace('.sqlite', '.json')
    with open(input_file_nobuf, 'w') as f:
        json.dump(nobuf_template, f)
    s = subprocess.check_output(['cyclus', '-o', output_file_nobuf, input_file_nobuf],
                                universal_newlines=True, env=ENV)
    with open(input_file_yesbuf, 'w') as f:
        json.dump(yesbuf_template, f)
    s = subprocess.check_output(['cyclus', '-o', output_file_yesbuf, input_file_yesbuf],
                                universal_newlines=True, env=ENV)
    
    # check if calculated demand is 20% higher for yesbuf case
    cur_nobuf = functions.get_cursor(output_file_nobuf)
    cur_yesbuf = functions.get_cursor(output_file_yesbuf)
    calcdemand_nobuf = cur_nobuf.execute("select time, value from timeseriescalc_demandpower").fetchall()
    calcdemand_yesbuf = cur_yesbuf.execute("select time, value from timeseriescalc_demandpower").fetchall()
    count = 0
    for x in range(len(calcdemand_nobuf)):
        if calcdemand_nobuf[x][0] != calcdemand_yesbuf[x][0]:
            count +=1
    
    assert(count == 0)