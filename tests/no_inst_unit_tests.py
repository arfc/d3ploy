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

# set error tolerance. 1 means 1 source capacity
tol = 1


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


def cleanup():
    """ Removes the generated input file and output sqlite database file."""
    if os.path.exists(output_file):
        os.remove(output_file)
    if os.path.exists(input_file):
        os.remove(input_file)


# the TEMPLATE is a dictionary of all simulation parameters
# except the region-institution definition
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
            "config": {"Sink": {"in_commods": {"val": "spent_uox"},
                                "max_inv_size": 1,
                                "sink_record_demand": "fuel_cap"}},
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
                    "refuel_time": "0",
                    "reactor_fuel_demand": "fuel_reactor"
                }
            },
            "name": "reactor"
        }]
    }
}

# testA refers to if NOInst meets the increased demand by
# deploying more facilities.
# testB refers to if NOInst meets the decreased demand by
# decommissioning existing facilities.


# TestA Examples

# Test A_1
INIT_DEMAND = copy.deepcopy(TEMPLATE)
INIT_DEMAND["simulation"].update({"region": {
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


@pytest.mark.base
def test_a1_init_demand():
    # tests if NOInst deploys a source
    # given initial demand and no initial facilities
    output_file = 'init_file.sqlite'
    input_file = output_file.replace('.sqlite', '.json')
    with open(input_file, 'w') as f:
        json.dump(INIT_DEMAND, f)
    s = subprocess.check_output(['cyclus', '-o', output_file, input_file],
                                universal_newlines=True, env=ENV)
    # check if ran successfully
    assert("Cyclus run successful!" in s)

    # getting the sqlite file
    cur = get_cursor(output_file)
    query = 'SELECT count(*) FROM agententry WHERE Prototype = "source"'

    # check base solution
    source_base = cur.execute(query).fetchone()
    assert(1 <= source_base[0] <= (1 + tol))


@pytest.mark.exact
def test_a1_init_demand_exact():
    output_file = 'init_file.sqlite'
    cur = get.cursor(output_file)
    # check exact solution
    source_exact = cur.execute(query + " AND EnterTime = 1").fetchone()
    assert(source_exact[0] == 1)


# Test A_2
INIT_DEMAND_WITH_INIT_FACILITIES = copy.deepcopy(TEMPLATE)
INIT_DEMAND_WITH_INIT_FACILITIES["simulation"].update({"region": {
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
        "initialfacilitylist": {
            "entry": {"number": 1,
                      "prototype": "source"}
        },
        "name": "source_inst"
    },
    "name": "SingleRegion"
}
}
)


@pytest.mark.base
def test_a2_init_demand_with_init_facilities():
    # tests if NOInst deploys a source given
    # initial demand and no initial facilities
    output_file = 'init_demand_init_fac.sqlite'
    input_file = output_file.replace('.sqlite', '.json')
    with open(input_file, 'w') as f:
        json.dump(INIT_DEMAND_WITH_INIT_FACILITIES, f)
    s = subprocess.check_output(['cyclus', '-o', output_file, input_file],
                                universal_newlines=True, env=ENV)
    # check if ran successfully
    assert("Cyclus run successful!" in s)

    # getting the sqlite file
    cur = get_cursor(output_file)
    query = 'SELECT count(*) FROM agententry WHERE Prototype = "source"'

    # check base solution
    source_base = cur.execute(query).fetchone()
    assert(2 <= source_base[0] <= (2 + tol))


@pytest.mark.exact
def test_a2_init_demand_with_init_facilities_exact():
    output_file = 'init_demand_init_fac.sqlite'
    cur = get_cursor(outputfile)
    source_exact = cur.execute(query + " AND EnterTime = 1").fetchone()
    assert(source_exact[0] == 1)


# Test A_3
INCREASING_DEMAND = copy.deepcopy(TEMPLATE)
INCREASING_DEMAND['simulation'].update(
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


@pytest.mark.base
def test_a3_increasing_demand():
    # tests if NOInst deploys a source according to increasing demand
    output_file = 'increasing_demand.sqlite'
    input_file = output_file.replace('.sqlite', '.json')
    with open(input_file, 'w') as f:
        json.dump(INCREASING_DEMAND, f)
    s = subprocess.check_output(['cyclus', '-o', output_file, input_file],
                                universal_newlines=True, env=ENV)
    # check if ran successfully
    assert("Cyclus run successful!" in s)

    # getting the sqlite file
    cur = get_cursor(output_file)
    query = "SELECT count(*) FROM agententry WHERE Prototype = 'source'"

    # check base solution
    source_base = cur.execute(query).fetchone()
    assert(3 <= source_base[0] <= (3 + tol))


@pytest.mark.exact
def test_a3_increasing_demand_exact():
    output_file = 'increasing_demand.sqlite'
    cur = get_cursor(output_file)
    source_exact1 = cur.execute(query + " AND EnterTime = 1").fetchone()
    assert(source_exact1[0] == 2)
    source_exact2 = cur.execute(query + " AND EnterTime = 12").fetchone()
    assert(source_exact2[0] == 1)


# Test A_4
INCREASING_DEMAND_WITH_INIT_FACILITIES = copy.deepcopy(TEMPLATE)
INCREASING_DEMAND_WITH_INIT_FACILITIES['simulation'].update(
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
            "initialfacilitylist": {
                "entry": {"number": 1,
                          "prototype": "source"}
            },
            "name": "source_inst"
        },
        "name": "SingleRegion"
    }}
)


@pytest.mark.base
def test_a4_increasing_demand_with_init_facilities():
    # tests if NOInst deploys a source according to increasing demand
    output_file = 'increasing_demand_with_init_facilites.sqlite'
    input_file = output_file.replace('.sqlite', '.json')
    with open(input_file, 'w') as f:
        json.dump(INCREASING_DEMAND_WITH_INIT_FACILITIES, f)
    s = subprocess.check_output(['cyclus', '-o', output_file, input_file],
                                universal_newlines=True, env=ENV)

    # check if ran successfully
    assert("Cyclus run successful!" in s)

    # getting the sqlite file
    cur = get_cursor(output_file)
    query = "SELECT count(*) FROM agententry WHERE Prototype = 'source'"

    # check base solution
    source_base = cur.execute(query).fetchone()
    assert(3 <= source_base[0] <= (3 + tol))


@pytest.mark.exact
def test_a4_increasing_demand_with_init_facilities_exact():
    output_file = 'increasing_demand_with_init_facilites.sqlite'
    cur = get_cursor(output_file)
    source_exact1 = cur.execute(query + " AND EnterTime = 1").fetchone()
    assert(source_exact1[0] == 2)
    source_exact2 = cur.execute(query + " AND EnterTime = 12").fetchone()
    assert(source_exact2[0] == 1)


# Test A_5
REACTOR_SOURCE_INIT_DEMAND = copy.deepcopy(TEMPLATE)
REACTOR_SOURCE_INIT_DEMAND['simulation'].update(
    {"region": {
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


@pytest.mark.base
def test_a5_reactor_source_init_demand():
    # tests if the reactor and source pair is
    # correctly deployed in static demand
    output_file = 'reactor_source_init_demand.sqlite'
    input_file = output_file.replace('.sqlite', '.json')
    with open(input_file, 'w') as f:
        json.dump(REACTOR_SOURCE_INIT_DEMAND, f)
    s = subprocess.check_output(['cyclus', '-o', output_file, input_file],
                                universal_newlines=True, env=ENV)
    # check if ran successfully
    assert("Cyclus run successful!" in s)

    # getting the sqlite file
    cur = get_cursor(output_file)
    query = "SELECT count(*) FROM agententry WHERE Prototype = 'reactor'"

    # check base solution
    reactor_base = cur.execute(query).fetchone()
    assert(1 <= reactor_base[0] <= 1 + tol)
    source_base = cur.execute(query.replace('reactor', 'source')).fetchone()
    assert(1 <= source_base[0] <= 1 + tol)


@pytest.mark.exact
def test_a5_reactor_source_init_demand_exact():
    output_file = 'reactor_source_init_demand.sqlite'
    cur = get_cursor(output_file)
    reactor_exact = cur.execute(query + " AND EnterTime = 1").fetchone()
    assert(reactor_exact[0] == 1)
    source_exact = cur.execute(query.replace(
        'reactor', 'source') + " AND EnterTime = 1").fetchone()
    assert(source_exact[0] == 1)



# Test A_6
REACTOR_SOURCE_INIT_DEMAND_WITH_INIT_FACILITIES = copy.deepcopy(TEMPLATE)
REACTOR_SOURCE_INIT_DEMAND_WITH_INIT_FACILITIES['simulation'].update(
    {"region": {
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
                "initialfacilitylist": {
                    "entry": {"number": 1,
                              "prototype": "source"}
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

                "initialfacilitylist": {
                    "entry": {"number": 1,
                              "prototype": "reactor"}
                },
                "name": "reactor_inst"
            }
        ],
        "name": "SingleRegion"
    }}
)


@pytest.mark.base
def test_a6_reactor_source_init_demand_with_init_facilities():
    # tests if the reactor and source pair is correctly
    # deployed in static demand
    output_file = 'reactor_source_init_demand_with_init_facilities.sqlite'
    input_file = output_file.replace('.sqlite', '.json')
    with open(input_file, 'w') as f:
        json.dump(REACTOR_SOURCE_INIT_DEMAND_WITH_INIT_FACILITIES, f)
    s = subprocess.check_output(['cyclus', '-o', output_file, input_file],
                                universal_newlines=True, env=ENV)
    # check if ran successfully
    assert("Cyclus run successful!" in s)

    # getting the sqlite file
    cur = get_cursor(output_file)
    query = "SELECT count(*) FROM agententry WHERE Prototype = 'reactor'"

    # check base solution
    reactor_base = cur.execute(query).fetchone()
    assert(1 <= reactor_base[0] <= 1 + tol)
    source_base = cur.execute(query.replace('reactor', 'source')).fetchone()
    assert(1 <= source_base[0] <= 1 + tol)


@pytest.mark.exact
def test_a6_reactor_source_init_demand_with_init_facilities():
    output_file = 'reactor_source_init_demand_with_init_facilities.sqlite'
    cur = get_cursor(output_file)
    reactor_exact = cur.execute(query + " AND EnterTime = 1").fetchone()
    assert(reactor_exact[0] == 1)
    source_exact = cur.execute(query.replace(
        'reactor', 'source') + " AND EnterTime = 1").fetchone()
    assert(source_exact[0] == 1)


# Test A_7
REACTOR_SOURCE_GROWTH = copy.deepcopy(TEMPLATE)
REACTOR_SOURCE_GROWTH['simulation'].update(
    {"region": {
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

# Test A_7


@pytest.mark.base
def test_a7_reactor_source_growth():
    # tests if the reactor and source pair is correctly
    # deployed with increase in demand
    output_file = 'reactor_source_growth.sqlite'
    input_file = output_file.replace('.sqlite', '.json')
    with open(input_file, 'w') as f:
        json.dump(REACTOR_SOURCE_GROWTH, f)
    s = subprocess.check_output(['cyclus', '-o', output_file, input_file],
                                universal_newlines=True, env=ENV)
    # check if ran successfully
    assert("Cyclus run successful!" in s)

    # getting the sqlite file
    cur = get_cursor(output_file)
    query = "SELECT count(*) FROM agententry WHERE Prototype = 'source'"

    # check base solution
    source_base = cur.execute(query).fetchone()
    assert(3 <= source_base[0] <= (3 + tol))
    reactor_base = cur.execute(query.replace('source', 'reactor')).fetchon()
    assert(3 <= reactor_base[0] <= (3 + tol))


@pytest.mark.exact
def test_a7_reactor_source_growth_exact():
    output_file = 'reactor_source_growth.sqlite'
    cur = get_cursor(output_file)
    source_exact1 = cur.execute(query + " AND EnterTime = 1").fetchone()
    assert(source_exact1[0] == 2)
    source_exact2 = cur.execute(query + " AND EnterTime = 12").fetchone()
    assert(source_exact2[0] == 1)
    source_exact1 = cur.execute(query.replace(
        'source', 'reactor') + " AND EnterTime = 1").fetchone()
    assert(source_exact1[0] == 2)
    source_exact2 = cur.execute(query.replace(
        'source', 'reactor') + " AND EnterTime = 12").fetchone()
    assert(source_exact2[0] == 1)

# TestB examples


# Test B_1
PHASEOUT_NO_INITDEMAND = copy.deepcopy(TEMPLATE)
PHASEOUT_NO_INITDEMAND["simulation"].update(
    {"region": {
        "config": {"NullRegion": "\n      "},
        "institution": {
            "config": {
                "NOInst": {
                    "calc_method": "arma",
                    "demand_commod": "POWER",
                    "demand_std_dev": "0.0",
                    "growth_rate": "0",
                    "initial_demand": "0",
                    "prototypes": {"val": "source"},
                    "steps": "1",
                    "supply_commod": "fuel"
                }
            },
            "initialfacilitylist": {
                "entry": {"number": 1,
                          "prototype": "source"}
            },
            "name": "source_inst"
        },
        "name": "SingleRegion"
    }}
)


def test_b1_phaseout_no_initdemand():
    # tests if NOInst decomissions all deployed
    # facilities with demand going to zero.
    output_file = 'phaseout_no_initdemand.sqlite'
    input_file = output_file.replace('.sqlite', '.json')
    with open(input_file, 'w') as f:
        json.dump(PHASEOUT_NO_INITDEMAND, f)
    s = subprocess.check_output(['cyclus', '-o', output_file, input_file],
                                universal_newlines=True, env=ENV)
    # check if ran successfully
    assert("Cyclus run successful!" in s)

    # getting the sqlite file
    cur = get_cursor(output_file)
    # check if 1 source facility has been decommissioned
    source = cur.execute(
        "SELECT count(*) FROM agentexit WHERE ExitTime = 2").fetchone()
    assert(source[0] == 1)


# Test B_2
PHASEOUT = copy.deepcopy(TEMPLATE)
PHASEOUT["simulation"].update(
    {"region": {
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
            "initialfacilitylist": {
                "entry": {"number": 1,
                          "prototype": "source"}
            },
            "name": "source_inst"
        },
        "name": "SingleRegion"
    }}
)


def test_b2_phaseout():
    # tests if NOInst decomissions all deployed
    # facilities with demand going to zero.
    output_file = 'phaseout.sqlite'
    input_file = output_file.replace('.sqlite', '.json')
    with open(input_file, 'w') as f:
        json.dump(PHASEOUT, f)
    s = subprocess.check_output(['cyclus', '-o', output_file, input_file],
                                universal_newlines=True, env=ENV)
    # check if ran successfully
    assert("Cyclus run successful!" in s)

    # getting the sqlite file
    cur = get_cursor(output_file)
    # check if 1 source facility has been decommissioned
    source = cur.execute(
        "SELECT count(*) FROM agentexit WHERE ExitTime = 13").fetchone()
    assert(source[0] == 1)
