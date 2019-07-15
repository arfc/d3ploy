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
import operator


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


def supply_demand_dict_driving(sqlite, demand_eq, commod):
    """ Puts supply, demand, calculated demand and
    calculated supply into a nice dictionary format
    if given the sql file, demand_eq of driving commodity
    and commodity name
    for a driving commodity
    Parameters
    ----------
    sqlite: sql file to analyze
    demand_eq: string of demand equation
    commod: string of commod name
    Returns
    -------
    returns 4 dicts: dictionaries of supply, demand, calculated
    demand and calculated supply
    """
    cur = get_cursor(sqlite)
    tables = {}
    tables[0] = "timeseriessupply" + commod
    tables[1] = "timeseriescalc_demand" + commod
    tables[2] = "timeseriescalc_supply" + commod
    fuel_supply = cur.execute(
        "select time, sum(value) from " +
        tables[0] +
        " group by time").fetchall()
    calc_fuel_demand = cur.execute(
        "select time, sum(value) from " +
        tables[1] +
        " group by time").fetchall()
    calc_fuel_supply = cur.execute(
        "select time, sum(value) from " +
        tables[2] +
        " group by time").fetchall()
    dict_demand = {}
    dict_supply = {}
    dict_calc_demand = {}
    dict_calc_supply = {}
    for x in range(0, len(fuel_supply)):
        dict_supply[fuel_supply[x][0]] = fuel_supply[x][1]
    for x in range(0, len(calc_fuel_demand)):
        dict_calc_demand[calc_fuel_demand[x][0]] = calc_fuel_demand[x][1]
    for x in range(0, len(calc_fuel_supply)):
        dict_calc_supply[calc_fuel_supply[x][0]] = calc_fuel_supply[x][1]
    oldt = np.fromiter(dict_supply.keys(), dtype=float)
    t = np.arange(0, oldt[-1] + 1)
    fuel_demand = eval(demand_eq)
    if isinstance(fuel_demand, int):
        fuel_demand = fuel_demand * np.ones(len(t))
    for x in range(0, len(t)):
        dict_demand[t[x]] = fuel_demand[x]
    
    # give dict supply zeros at timesteps 1 and 2 
    for key in dict_demand.keys():
        if key not in dict_supply:
            dict_supply[key] = 0.0

    # give dict supply zeros at timesteps 1 and 2
    for key in dict_demand.keys():
        if key not in dict_supply:
            dict_supply[key] = 0.0

    all_dict = {}
    all_dict['dict_demand'] = dict_demand
    all_dict['dict_supply'] = dict_supply
    all_dict['dict_calc_demand'] = dict_calc_demand
    all_dict['dict_calc_supply'] = dict_calc_supply

    return all_dict


def supply_demand_dict_nondriving(sqlite, commod, demand_driven):
    """ Puts supply, demand, calculated demand and
    calculated supply into a nice dictionary format
    if given the sql file and commodity name
    for a non-driving commodity
    Parameters
    ----------
    sqlite: sql file to analyze
    commod: string of commod name
    demand_driven: Boolean. If true, the commodity is demand driven,
    if false, the commodity is supply driven
    Returns
    -------
    returns 4 dicts: dictionaries of supply, demand, calculated
    demand and calculated supply
    """
    cur = get_cursor(sqlite)
    tables = {}
    tables[0] = "timeseriessupply" + commod
    tables[2] = "timeseriescalc_supply" + commod
    tables[3] = "timeseriesdemand" + commod
    if demand_driven:
        tables[1] = "timeseriescalc_demand" + commod
    else:
        tables[1] = "timeseriescalc_capacity" + commod
    fuel_demand = cur.execute(
        "select time, sum(value) from " +
        tables[3] +
        " group by time").fetchall()
    fuel_supply = cur.execute(
        "select time, sum(value) from " +
        tables[0] +
        " group by time").fetchall()
    calc_fuel_demand = cur.execute(
        "select time, sum(value) from " +
        tables[1] +
        " group by time").fetchall()
    calc_fuel_supply = cur.execute(
        "select time, sum(value) from " +
        tables[2] +
        " group by time").fetchall()
    dict_demand = {}
    dict_supply = {}
    dict_calc_demand = {}
    dict_calc_supply = {}
    for x in range(0, len(fuel_supply)):
        dict_supply[fuel_supply[x][0]] = fuel_supply[x][1]
    for x in range(0, len(calc_fuel_demand)):
        dict_calc_demand[calc_fuel_demand[x][0]] = calc_fuel_demand[x][1]
    for x in range(0, len(calc_fuel_supply)):
        dict_calc_supply[calc_fuel_supply[x][0]] = calc_fuel_supply[x][1]

    t = np.fromiter(dict_supply.keys(), dtype=float)
    for x in range(0, len(t)):
        dict_demand[t[x]] = 0

    for x in range(0, len(fuel_demand)):
        dict_demand[fuel_demand[x][0]] = fuel_demand[x][1]

    # give dict supply zeros at timesteps 1 and 2
    for key in dict_demand.keys():
        if key not in dict_supply:
            dict_supply[key] = 0.0

    all_dict = {}
    all_dict['dict_demand'] = dict_demand
    all_dict['dict_supply'] = dict_supply
    all_dict['dict_calc_demand'] = dict_calc_demand
    all_dict['dict_calc_supply'] = dict_calc_supply

    return all_dict


def supply_demand_dict_nond3ploy(sqlite, commod, demand_eq=0):
    """ Puts supply and demand into a nice dictionary format
    if given the sql file and commodity name
    Parameters
    ----------
    sqlite: sql file to analyze
    commod: string of commod name
    demand_eq: provide a demand eq is the commodity is 'power'
    Returns
    -------
    returns 2 dicts: dictionaries of supply and demand
    """
    cur = get_cursor(sqlite)
    tables = {}
    all_dict = {}

    tables[0] = "timeseriessupply" + commod
    fuel_supply = cur.execute(
        "select time, sum(value) from " +
        tables[0] +
        " group by time").fetchall()
    dict_supply = {}
    for x in range(0, len(fuel_supply)):
        dict_supply[fuel_supply[x][0]] = fuel_supply[x][1]
    all_dict['dict_supply'] = dict_supply

    dict_demand = {}
    if commod.lower() == 'power':
        oldt = np.fromiter(dict_supply.keys(), dtype=float)
        t = np.arange(0, oldt[-1] + 1)
        fuel_demand = eval(demand_eq)
        if isinstance(fuel_demand, int):
            fuel_demand = fuel_demand * np.ones(len(t))
        for x in range(0, len(t)):
            dict_demand[t[x]] = fuel_demand[x]
    else:
        tables[1] = "timeseriesdemand" + commod
        fuel_demand = cur.execute(
            "select time, sum(value) from " + tables[1] +
            " group by time").fetchall()
        for x in range(0, len(fuel_demand)):
            dict_demand[fuel_demand[x][0]] = fuel_demand[x][1]
    all_dict['dict_demand'] = dict_demand

    return all_dict


def cumulative_undersupply(all_dict):
    """obtains the cumulative undersupply over time
    Parameters
    ----------
    all_dict: dict
        a dictionary containing two timeseries dictionaries
        (dict_supply and dict_demand) which contains supply
        and demand values respectively.
    Returns
    -------
    cumulative: float
        The cumulative difference between demand and supply
        if demand is larger than supply. 0 otherwise.
    """
    dict_demand = all_dict['dict_demand']
    dict_supply = all_dict['dict_supply']

    cumulative = 0
    for step in set().union(dict_demand.keys(), dict_supply.keys()):
        try:
            if dict_supply[step] <= dict_demand[step]:
                cumulative += (dict_demand[step] - dict_supply[step])
        except KeyError:
            cumulative += 0
    return cumulative


def cumulative_oversupply(all_dict):
    """btains the cumulative oversupply over time
    Parameters
    ----------
    all_dict: dict
        a dictionary containing two timeseries dictionaries
        (dict_supply and dict_demand) which contains supply
        and demand values respectively.
    Returns
    -------
    cumulative: float
        The cumulative difference between supply and demand
        if supply is larger than demand. 0 otherwise.
    """
    dict_demand = all_dict['dict_demand']
    dict_supply = all_dict['dict_supply']

    cumulative = 0
    for step in set().union(dict_demand.keys(), dict_supply.keys()):
        try:
            if dict_supply[step] > dict_demand[step]:
                cumulative += (dict_supply[step] - dict_demand[step])
        except KeyError:
            cumulative += 0
    return cumulative


def chi_goodness_test(all_dict):
    """ Conducts a chi2 goodness of fit test
    Parameters
    ----------
    dict_demand: timeseries dictionary of demand values
    dict_supply: timeseries dictionary of supply values
    Returns
    -------
    returns an int of the chi2 (goodness of fit value) for
    the two input timeseries dictionaries
    """

    dict_demand = all_dict['dict_demand']
    dict_supply = all_dict['dict_supply']

    chi2 = 0
    start = int(list(dict_demand.keys())[0])
    for x in range(start - 1, len(dict_demand)):
        y = x + 1
        try:
            chi2 += (dict_supply[y] - dict_demand[y])**2 / dict_demand[y]
        except (ZeroDivisionError, KeyError) as e:
            chi2 += 0

    return chi2


def supply_under_demand(all_dict, demand_driven):
    """ Calculates the number of time steps supply is
    under demand
    Parameters
    ----------
    dict_demand: timeseries dictionary of demand values
    dict_supply: timeseries dictionary of supply values
    Returns
    -------
    returns an int of the number of time steps supply is
    under demand
    """

    dict_demand = all_dict['dict_demand']
    dict_supply = all_dict['dict_supply']

    num_under = 0

    for x in range(len(dict_demand)):
        if demand_driven:
            try:
                if dict_supply[x] < dict_demand[x]:
                    num_under = num_under + 1
            except KeyError:
                num_under += 0
        else:
            try:
                if dict_supply[x] > dict_demand[x]:
                    num_under = num_under + 1
            except KeyError:
                num_under += 0
    return num_under


def best_calc_method(in_dict, maximum):
    """ Calculates the number of time steps supply is
    under demand
    Parameters
    ----------
    in_dict: keys => calc methods, values => results from
    tests of each calc method (chi2 goodness of fit etc)
    max: true/false boolean, true => find max of in_dict,
    false => find min of in_dict
    Returns
    -------
    returns a list of the calc methods that have the max
    or min (depending on input) in the in_dict
    """
    if maximum:
        highest = max(in_dict.values())
        best = [k for k, v in in_dict.items() if v == highest]
    else:
        lowest = min(in_dict.values())
        best = [k for k, v in in_dict.items() if v == lowest]

    return best


def metrics(all_dict, metric_dict, calc_method, commod, demand_driven):
    # check if dictionary exists if not initialize
    value = metric_dict.get(commod + '_undersupply', 0)
    if value == 0:
        metric_dict[commod+'_cumulative_undersupply'] = {}
        metric_dict[commod+'_cumualtive_oversupply'] = {}
        #metric_dict[commod+'_chi2'] = {}
        metric_dict[commod + '_undersupply'] = {}

    metric_dict[commod + '_cumulative_undersupply'][calc_method] = \
        cumulative_undersupply(all_dict)
    metric_dict[commod + '_cumualtive_oversupply'][calc_method] = \
        cumulative_oversupply(all_dict)
    metric_dict[commod + '_undersupply'][calc_method] = \
        supply_under_demand(all_dict, demand_driven)

    return metric_dict


def get_agent_dict(sqlite_file, prototype_list):
    """ returns a dictionary of the number of prototypes `at play'
        at any given timestep """
    cur = get_cursor(sqlite_file)
    agent_dict = {}
    duration = cur.execute('SELECT duration FROM info').fetchone()[0]
    for proto in prototype_list:
        agententry = cur.execute(
            'SELECT entertime FROM agententry WHERE prototype = "%s"' %
            proto).fetchall()
        entertime_list = [item['entertime'] for item in agententry]
        try:
            agentexit = cur.execute(
                'SELECT exittime FROM agentexit ' +
                'INNER JOIN agententry ON agententry.agentid = agentexit.agentid ' +
                'WHERE prototype = "%s"' %
                proto).fetchall()
            exittime_list = [item['exittime'] for item in agentexit]
        except BaseException:
            exittime_list = []
        agent_dict[proto] = agents_at_play(
            entertime_list, exittime_list, duration)
    return agent_dict


def agents_at_play(entertime_list, exittime_list, duration):
    time_array = np.zeros(duration + 1)
    atplay = 0
    atplay_dict = {}
    for indx, n in enumerate(time_array):
        if indx in entertime_list:
            atplay += entertime_list.count(indx)
        if indx in exittime_list:
            atplay -= exittime_list.count(indx)
        atplay_dict[indx] = atplay
    return atplay_dict
