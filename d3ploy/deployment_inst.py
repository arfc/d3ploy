import random
import copy
import math
from collections import defaultdict
import numpy as np
import scipy as sp

from cyclus.agents import Institution, Agent
from cyclus import lib
import cyclus.typesystem as ts
import d3ploy.solver as solver
import d3ploy.NO_solvers as no
import d3ploy.DO_solvers as do


def build_dict(
        facility_commod,
        facility_capacity,
        facility_pref,
        facility_constraintcommod,
        facility_constraintval):
    facility_dict = {}
    commodity_dict = {}
    for key, val in facility_capacity.items():
        facility_dict[key] = {}
        facility_dict[key] = {'cap': val}
        if key in facility_pref.keys():
            facility_dict[key].update({'pref': facility_pref[key]})
        else:
            facility_dict[key].update({'pref': '0'})
        if key in facility_constraintcommod.keys():
            facility_dict[key].update(
                {'constraint_commod': facility_constraintcommod[key]})
        else:
            facility_dict[key].update({'constraint_commod': '0'})
        if key in facility_constraintval.keys():
            facility_dict[key].update(
                {'constraint': facility_constraintval[key]})
        else:
            facility_dict[key].update({'constraint': 0.0})
    for key, val in facility_commod.items():
        if val not in commodity_dict.keys():
            commodity_dict[val] = {}
        if key in facility_dict.keys():
            commodity_dict[val].update({key: facility_dict[key]})
    return commodity_dict


def build_buffer_dict(buffer, commods):
    buffer_dict = {}
    for i in commods:
        count = 0
        for key, value in buffer.items():
            if i == key:
                count += 1
                buffer_dict[key] = value
        if count == 0:
            buffer_dict[i] = 0.
    return buffer_dict


def build_buffer_type_dict(buffer, commods):
    buffer_dict = {}
    for i in commods:
        count = 0
        for key, value in buffer.items():
            if i == key:
                count += 1
                buffer_dict[key] = value
        if count == 0:
            buffer_dict[i] = "perc"
    return buffer_dict
