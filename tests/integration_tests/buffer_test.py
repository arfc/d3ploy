""" This python file contains supply buffer and capacity buffer tests
for DemandDrivenDeploymentInst and SupplyDrivenDeploymentInst
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


# ----------------------------------------------------------------------------- #
# This test will fail if the inclusion of a 20% supply buffer doesn't result in
# the calculated demand being 20% larger than a simulation without the supply
# buffer.

with open('buff_test.py', 'r') as f:
    buff_template = json.load(f)
f.close()

nobuf_template = buff_template
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


yesbuf_template = buff_template
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
                        {"commod": "POWER", "buffer": 0.2}
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
    s = subprocess.check_output(['cyclus',
                                 '-o',
                                 output_file_nobuf,
                                 input_file_nobuf],
                                universal_newlines=True,
                                env=ENV)
    with open(input_file_yesbuf, 'w') as f:
        json.dump(yesbuf_template, f)
    s = subprocess.check_output(['cyclus',
                                 '-o',
                                 output_file_yesbuf,
                                 input_file_yesbuf],
                                universal_newlines=True,
                                env=ENV)

    # check if calculated demand is 20% higher for yesbuf case
    cur_nobuf = functions.get_cursor(output_file_nobuf)
    cur_yesbuf = functions.get_cursor(output_file_yesbuf)
    calcdemand_nobuf = cur_nobuf.execute(
        "select time, value from timeseriescalc_demandpower").fetchall()
    calcdemand_yesbuf = cur_yesbuf.execute(
        "select time, value from timeseriescalc_demandpower").fetchall()
    count = 0
    for x in range(2):
        if 1.2 * calcdemand_nobuf[x][1] != calcdemand_yesbuf[x][1]:
            count += 1

    assert(count == 0)


# ----------------------------------------------------------------------------- #
# This test will fail if the inclusion of a 20% capacity buffer doesn't result in
# the calculated supply being 20% larger than a simulation without the capacity
# buffer.

nobuf_template2 = buff_template
nobuf_template2["simulation"].update({"region": {
    "config": {"NullRegion": "\n      "},
    "institution": [
        {
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
                            {"commod": "POWER", "buffer": "0.2"}
                        ]
                    },
                    "demand_eq": "3*t",
                    "record": "1",
                    "steps": "1"
                }
            },
            "name": "source_inst"
        },
        {
            "config": {
                "SupplyDrivenDeploymentInst": {
                    "calc_method": "ma",
                    "capacity_std_dev": "1.0",
                    "facility_capacity": {"item": {"capacity": "10", "facility": "sink"}},
                    "facility_commod": {"item": {"commod": "spent_uox", "facility": "sink"}},
                    "record": "1",
                    "steps": "1"
                }
            },
            "name": "hello_inst"
        }
    ],
    "name": "SingleRegion"
}
})


yesbuf_template2 = buff_template
yesbuf_template2["simulation"].update({"region": {
    "config": {"NullRegion": "\n      "},
    "institution": [
        {
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
                            {"commod": "POWER", "buffer": "0.2"}
                        ]
                    },
                    "demand_eq": "3*t",
                    "record": "1",
                    "steps": "1"
                }
            },
            "name": "source_inst"
        },
        {
            "config": {
                "SupplyDrivenDeploymentInst": {
                    "calc_method": "ma",
                    "capacity_std_dev": "1.0",
                    "facility_capacity": {"item": {"capacity": "10", "facility": "sink"}},
                    "facility_commod": {"item": {"commod": "spent_uox", "facility": "sink"}},
                    "capacity_buffer": {"item": {"commod": "spent_uox", "buffer": "0.2"}},
                    "record": "1",
                    "steps": "1"
                }
            },
            "name": "hello_inst"
        }
    ],
    "name": "SingleRegion"
}
})


def test_capacity_buffer():
    output_file_nobuf2 = 'nobuf2.sqlite'
    output_file_yesbuf2 = 'yesbuf2.sqlite'
    input_file_nobuf2 = output_file_nobuf2.replace('.sqlite', '.json')
    input_file_yesbuf2 = output_file_yesbuf2.replace('.sqlite', '.json')
    with open(input_file_nobuf2, 'w') as f:
        json.dump(nobuf_template2, f)
    s = subprocess.check_output(['cyclus',
                                 '-o',
                                 output_file_nobuf2,
                                 input_file_nobuf2],
                                universal_newlines=True,
                                env=ENV)
    with open(input_file_yesbuf2, 'w') as f:
        json.dump(yesbuf_template2, f)
    s = subprocess.check_output(['cyclus',
                                 '-o',
                                 output_file_yesbuf2,
                                 input_file_yesbuf2],
                                universal_newlines=True,
                                env=ENV)

    # check if calculated demand is 20% higher for yesbuf case
    cur_nobuf2 = functions.get_cursor(output_file_nobuf2)
    cur_yesbuf2 = functions.get_cursor(output_file_yesbuf2)
    calcsupply_nobuf2 = cur_nobuf2.execute(
        "select time, value from timeseriescalc_supplyspent_uox").fetchall()
    calcsupply_yesbuf2 = cur_yesbuf2.execute(
        "select time, value from timeseriescalc_supplyspent_uox").fetchall()
    count = 0
    for x in range(2):
        if 1.2 * calcsupply_nobuf2[x][1] != calcsupply_yesbuf2[x][1]:
            count += 1

    assert(count == 0)


# ----------------------------------------------------------------------------- #
# This test will fail if the inclusion of a 20% supply buffer doesn't result in
# the calculated demand being 20% larger than a simulation without the supply
# buffer.

nobuf_template3 = buff_template
nobuf_template3["simulation"].update({"region": {
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


yesbuf_template3 = buff_template
yesbuf_template3["simulation"].update({"region": {
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
                        {"commod": "POWER", "buffer": 0.2},
                        {"commod": "fuel", "buffer": 0.2}
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


def test_supply_buffer_two():
    output_file_nobuf3 = 'nobuf3.sqlite'
    output_file_yesbuf3 = 'yesbuf3.sqlite'
    input_file_nobuf3 = output_file_nobuf3.replace('.sqlite', '.json')
    input_file_yesbuf3 = output_file_yesbuf3.replace('.sqlite', '.json')
    with open(input_file_nobuf3, 'w') as f:
        json.dump(nobuf_template3, f)
    s = subprocess.check_output(['cyclus',
                                 '-o',
                                 output_file_nobuf3,
                                 input_file_nobuf3],
                                universal_newlines=True,
                                env=ENV)
    with open(input_file_yesbuf3, 'w') as f:
        json.dump(yesbuf_template3, f)
    s = subprocess.check_output(['cyclus',
                                 '-o',
                                 output_file_yesbuf3,
                                 input_file_yesbuf3],
                                universal_newlines=True,
                                env=ENV)

    # check if calculated demand is 20% higher for yesbuf case
    cur_nobuf3 = functions.get_cursor(output_file_nobuf3)
    cur_yesbuf3 = functions.get_cursor(output_file_yesbuf3)
    calcdemandpower_nobuf3 = cur_nobuf3.execute(
        "select time, value from timeseriescalc_demandpower").fetchall()
    calcdemandpower_yesbuf3 = cur_yesbuf3.execute(
        "select time, value from timeseriescalc_demandpower").fetchall()
    calcdemandfuel_nobuf3 = cur_nobuf3.execute(
        "select time, value from timeseriescalc_demandfuel").fetchall()
    calcdemandfuel_yesbuf3 = cur_yesbuf3.execute(
        "select time, value from timeseriescalc_demandfuel").fetchall()
    count = 0
    for x in range(2):
        if int(
                1.2 *
                calcdemandpower_nobuf3[x][1]) != int(
                calcdemandpower_yesbuf3[x][1]):
            count += 1
    for x in range(2):
        if calcdemandfuel_nobuf3[x][0] != calcdemandfuel_yesbuf3[x][0]:
            count += 1
    assert(count == 0)


# ----------------------------------------------------------------------------- #
# This test will fail if the inclusion of a 3MW value power supply buffer
# doesn't result in the calculated demand being 3MW larger than a simulation
# without the supply buffer.

nobuf_template4 = buff_template
nobuf_template4["simulation"].update({"region": {
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


yesbuf_template4 = buff_template
yesbuf_template4["simulation"].update({"region": {
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
                        {"commod": "POWER", "buffer": 3}
                    ]
                },
                "buffer_type": {
                    "item": [
                        {"commod": "POWER", "type": "abs"}
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


def test_supply_buffer_num():
    output_file_nobuf4 = 'nobuf4.sqlite'
    output_file_yesbuf4 = 'yesbuf4.sqlite'
    input_file_nobuf4 = output_file_nobuf4.replace('.sqlite', '.json')
    input_file_yesbuf4 = output_file_yesbuf4.replace('.sqlite', '.json')
    with open(input_file_nobuf4, 'w') as f:
        json.dump(nobuf_template4, f)
    s = subprocess.check_output(['cyclus',
                                 '-o',
                                 output_file_nobuf4,
                                 input_file_nobuf4],
                                universal_newlines=True,
                                env=ENV)
    with open(input_file_yesbuf4, 'w') as f:
        json.dump(yesbuf_template4, f)
    s = subprocess.check_output(['cyclus',
                                 '-o',
                                 output_file_yesbuf4,
                                 input_file_yesbuf4],
                                universal_newlines=True,
                                env=ENV)

    # check if calculated demand is 1000MW higher for yesbuf case
    cur_nobuf4 = functions.get_cursor(output_file_nobuf4)
    cur_yesbuf4 = functions.get_cursor(output_file_yesbuf4)
    calcdemand_nobuf4 = cur_nobuf4.execute(
        "select time, value from timeseriescalc_demandpower").fetchall()
    calcdemand_yesbuf4 = cur_yesbuf4.execute(
        "select time, value from timeseriescalc_demandpower").fetchall()
    count = 0
    for x in range(2):
        if (3 + calcdemand_nobuf4[x][1]) != calcdemand_yesbuf4[x][1]:
            count += 1

    assert(count == 0)


# ----------------------------------------------------------------------------- #
# This test will fail if the inclusion of a 3kg spent fuel capacity buffer doesn't
# result in the calculated supply being 20% larger than a simulation without the
# capacity buffer.

nobuf_template5 = buff_template
nobuf_template5["simulation"].update({"region": {
    "config": {"NullRegion": "\n      "},
    "institution": [
        {
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
                            {"commod": "POWER", "buffer": "0.2"}
                        ]
                    },
                    "demand_eq": "3*t",
                    "record": "1",
                    "steps": "1"
                }
            },
            "name": "source_inst"
        },
        {
            "config": {
                "SupplyDrivenDeploymentInst": {
                    "calc_method": "ma",
                    "capacity_std_dev": "1.0",
                    "facility_capacity": {"item": {"capacity": "10", "facility": "sink"}},
                    "facility_commod": {"item": {"commod": "spent_uox", "facility": "sink"}},
                    "record": "1",
                    "steps": "1"
                }
            },
            "name": "hello_inst"
        }
    ],
    "name": "SingleRegion"
}
})


yesbuf_template5 = buff_template
yesbuf_template5["simulation"].update({"region": {
    "config": {"NullRegion": "\n      "},
    "institution": [
        {
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
                            {"commod": "POWER", "buffer": "0.2"}
                        ]
                    },
                    "demand_eq": "3*t",
                    "record": "1",
                    "steps": "1"
                }
            },
            "name": "source_inst"
        },
        {
            "config": {
                "SupplyDrivenDeploymentInst": {
                    "calc_method": "ma",
                    "capacity_std_dev": "1.0",
                    "facility_capacity": {"item": {"capacity": "10", "facility": "sink"}},
                    "facility_commod": {"item": {"commod": "spent_uox", "facility": "sink"}},
                    "capacity_buffer": {"item": {"commod": "spent_uox", "buffer": "3"}},
                    "buffer_type": {"item": {"commod": "spent_uox",
                                             "type": "abs"}},
                    "record": "1",
                    "steps": "1"
                }
            },
            "name": "hello_inst"
        }
    ],
    "name": "SingleRegion"
}
})


def test_capacity_buffer_num():
    output_file_nobuf5 = 'nobuf5.sqlite'
    output_file_yesbuf5 = 'yesbuf5.sqlite'
    input_file_nobuf5 = output_file_nobuf5.replace('.sqlite', '.json')
    input_file_yesbuf5 = output_file_yesbuf5.replace('.sqlite', '.json')
    with open(input_file_nobuf5, 'w') as f:
        json.dump(nobuf_template5, f)
    s = subprocess.check_output(['cyclus',
                                 '-o',
                                 output_file_nobuf5,
                                 input_file_nobuf5],
                                universal_newlines=True,
                                env=ENV)
    with open(input_file_yesbuf5, 'w') as f:
        json.dump(yesbuf_template5, f)
    s = subprocess.check_output(['cyclus',
                                 '-o',
                                 output_file_yesbuf5,
                                 input_file_yesbuf5],
                                universal_newlines=True,
                                env=ENV)

    # check if calculated demand is 20% higher for yesbuf case
    cur_nobuf5 = functions.get_cursor(output_file_nobuf5)
    cur_yesbuf5 = functions.get_cursor(output_file_yesbuf5)
    calcsupply_nobuf5 = cur_nobuf5.execute(
        "select time, value from timeseriescalc_supplyspent_uox").fetchall()
    calcsupply_yesbuf5 = cur_yesbuf5.execute(
        "select time, value from timeseriescalc_supplyspent_uox").fetchall()
    count = 0
    for x in range(2):
        if (3 + calcsupply_nobuf5[x][1]) != calcsupply_yesbuf5[x][1]:
            count += 1

    assert(count == 0)


# -------------------------------------------------------------------------- #
# This test will fail if the inclusion of a 3MW value power supply buffer
# with a supply_buffer_length of 5 time steps doesn't result in
# a) the calculated demand being 3MW larger than a simulation
#   without the supply buffer at time < supply_buffer_length
# b) the calculated demand being equivalent to a simulation
#   without the supply buffer at time >= supply_buffer_length

with open('buff_test_length.py', 'r') as f:
    buff_template = json.load(f)
f.close()

nobuf_template_length = buff_template
nobuf_template_length["simulation"].update({"region": {
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
                "demand_eq": "10",
                "record": "1",
                "steps": "10"
            }
        },
        "name": "source_inst"
    },
    "name": "SingleRegion"
}
})


yesbuf_template_length = buff_template
yesbuf_template_length["simulation"].update({"region": {
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
                        {"commod": "POWER", "buffer": 3}
                    ]
                },
                "supply_buffer_length": {
                    "item": [
                        {"commod": "POWER", "length": 5}
                    ]
                },
                "buffer_type": {
                    "item": [
                        {"commod": "POWER", "type": "abs"}
                    ]
                },
                "demand_eq": "10",
                "record": "1",
                "steps": "10"
            }
        },
        "name": "source_inst"
    },
    "name": "SingleRegion"
}
})


def test_supply_buffer_length():
    output_file_nobuf_length = 'nobuf_length.sqlite'
    output_file_yesbuf_length = 'yesbuf_length.sqlite'
    input_file_nobuf_length = output_file_nobuf_length.replace(
        '.sqlite', '.json')
    input_file_yesbuf_length = output_file_yesbuf_length.replace(
        '.sqlite', '.json')
    with open(input_file_nobuf_length, 'w') as f:
        json.dump(nobuf_template_length, f)
    s = subprocess.check_output(['cyclus',
                                 '-o',
                                 output_file_nobuf_length,
                                 input_file_nobuf_length],
                                universal_newlines=True,
                                env=ENV)
    with open(input_file_yesbuf_length, 'w') as f:
        json.dump(yesbuf_template_length, f)
    s = subprocess.check_output(['cyclus',
                                 '-o',
                                 output_file_yesbuf_length,
                                 input_file_yesbuf_length],
                                universal_newlines=True,
                                env=ENV)

    # check if calculated demand is 3 W higher for yesbuf case
    cur_nobuf_length = functions.get_cursor(output_file_nobuf_length)
    cur_yesbuf_length = functions.get_cursor(output_file_yesbuf_length)
    calcdemand_nobuf_len = cur_nobuf_length.execute(
        "select time, value from timeseriescalc_demandpower").fetchall()
    calcdemand_yesbuf_len = cur_yesbuf_length.execute(
        "select time, value from timeseriescalc_demandpower").fetchall()
    count = 0
    for x in range(0, 6):
        if (3 + calcdemand_nobuf_len[x][1]) != calcdemand_yesbuf_len[x][1]:
            count += 1
    for x in range(6, 10):
        if calcdemand_nobuf_len[x][1] != calcdemand_yesbuf_len[x][1]:
            count += 1

    assert(count == 0)
