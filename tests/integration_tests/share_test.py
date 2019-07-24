""" This python file contains tests for d3ploy's sharing capability
of one commodity between different facilities, for both
DemandDrivenDeploymentInst and SupplyDrivenDeploymentInst
archetypes.
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
                {"lib": "agents", "name": "NullInst"},
                {"lib": "cycamore", "name": "Source"},
                {"lib": "cycamore", "name": "Reactor"},
                {"lib": "cycamore", "name": "Sink"},
                {"lib": "d3ploy.demand_driven_deployment_inst",
                 "name": "DemandDrivenDeploymentInst"},
                {"lib": "d3ploy.supply_driven_deployment_inst",
                 "name": "SupplyDrivenDeploymentInst"}
            ]
        },
        "control": {"duration": "4", "startmonth": "1", "startyear": "2000"},
        "facility": [
            {
                "config": {"Source": {"outcommod": "sourceout",
                                      "outrecipe": "sourceoutrecipe",
                                                   "throughput": "1E5"}},
                "name": "source"
            },
            {
                "config": {"Sink": {"in_commods": {"val": "reactorout"},
                                    "max_inv_size": "1E6"}},
                "name": "sink"
            },
            {
                "config": {
                    "Reactor": {
                        "assem_size": "100",
                        "cycle_time": "1",
                        "fuel_incommods": {"val": "sourceout"},
                        "fuel_inrecipes": {"val": "sourceoutrecipe"},
                        "fuel_outcommods": {"val": "reactorout"},
                        "fuel_outrecipes": {"val": "reactoroutrecipe"},
                        "n_assem_batch": "1",
                        "n_assem_core": "1",
                        "power_cap": "2",
                        "refuel_time": "0"
                    }
                },
                "name": "reactor1"
            },
            {
                "config": {
                    "Reactor": {
                        "assem_size": "100",
                        "cycle_time": "1",
                        "fuel_incommods": {"val": "sourceout"},
                        "fuel_inrecipes": {"val": "sourceoutrecipe"},
                        "fuel_outcommods": {"val": "reactorout"},
                        "fuel_outrecipes": {"val": "reactoroutrecipe"},
                        "n_assem_batch": "1",
                        "n_assem_core": "1",
                        "power_cap": "3",
                        "refuel_time": "0"
                    }
                },
                "name": "reactor2"
            }
        ],
        "recipe": [
            {
                "basis": "mass",
                "name": "sourceoutrecipe",
                "nuclide": [{"comp": "0.711", "id": "U235"},
                            {"comp": "99.289", "id": "U238"}]
            },
            {
                "basis": "mass",
                "name": "reactoroutrecipe",
                "nuclide": [{"comp": "50", "id": "Kr85"},
                            {"comp": "50", "id": "Cs137"}]
            }
        ]
    }
}


# ------------------------------------------------------------------ #
# Two prototypes of reactor are deployed. They produce 2 and 3 MW,
# respectively. The sharing percentages are 40 and 60%. The
# power demand increases by 10 MW every timestep. Then to meet
# the demand, two reactors of each type has to be deployed.
# This test will fail if at any time step two of each type of
# reactor are not deployed.

share_template = copy.deepcopy(TEMPLATE)
share_template["simulation"].update({"region": {
    "config": {"NullRegion": "\n      "},
    "institution": [
    {
       "config": {"NullInst": "\n      "},
       "initialfacilitylist": {
           "entry": [
               {"number": "1", "prototype": "source"},
               {"number": "1", "prototype": "sink"}
           ]
       },
       "name": "sink_source_facilities"
    },
    {
    "config": {
            "DemandDrivenDeploymentInst": {
                "calc_method": "ma",
                "facility_capacity": {
                    "item": [
                        {"capacity": "2", "facility": "reactor1"},
                        {"capacity": "3", "facility": "reactor2"}
                    ]
                },
                "facility_commod": {
                    "item": [
                        {"commod": "POWER", "facility": "reactor1"},
                        {"commod": "POWER", "facility": "reactor2"}
                    ]
                },
                "facility_sharing": {
                    "item": [
                        {"percentage": "40", "facility": "reactor1"},
                        {"percentage": "60", "facility": "reactor2"}
                    ]
                },
                "demand_eq": "10*t",
            }
        },
         "name": "reactor_inst"
    }
    ],
    "name": "SingleRegion"
}
})


def test_supply_buffer():
    output_file_share = 'share.sqlite'
    input_file_share = output_file_share.replace('.sqlite', '.json')
    with open(input_file_share, 'w') as f:
        json.dump(share_template, f)

    s = subprocess.check_output(['cyclus',
                                 '-o',
                                 output_file_share,
                                 input_file_share],
                                universal_newlines=True,
                                env=ENV)

    # check number of reactors deployed
    cur_share = functions.get_cursor(output_file_share)

    reactors = cur_share.execute("select entertime, prototype from " +
                                 "agententry where prototype = " +
                                 "'reactor1' or prototype = " +
                                 "'reactor2'").fetchall()
    j = 0
    count_errors = 0
    for i in range(1, 4):
        count_reactor1 = 0
        count_reactor2 = 0
        while int(reactors[j][0]) <= i:
            if reactors[j][1] == 'reactor1':
                count_reactor1 += 1
            if reactors[j][1] == 'reactor2':
                count_reactor2 += 1
            j += 1
            if j == len(reactors):
                break
        if count_reactor1 != count_reactor2:
            count_errors += 1
    assert(count_errors == 0)
