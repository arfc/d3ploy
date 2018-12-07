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
    tables[0] = "timeseriessupply"+commod
    tables[1] = "timeseries"+commod+"calc_demand"
    tables[2] = "timeseries"+commod+"calc_supply"
    fuel_supply = cur.execute(
        "select time, sum(value) from "+tables[0]+" group by time").fetchall()
    calc_fuel_demand = cur.execute(
        "select time, sum(value) from "+tables[1]+" group by time").fetchall()
    calc_fuel_supply = cur.execute(
        "select time, sum(value) from "+tables[2]+" group by time").fetchall()
    dict_demand = {}
    dict_supply = {}
    dict_calc_demand = {}
    dict_calc_supply = {}
    for x in range(0, len(fuel_supply)):
        dict_supply[fuel_supply[x][0]] = fuel_supply[x][1]
        dict_calc_demand[fuel_supply[x][0]+1] = calc_fuel_demand[x][1]
        dict_calc_supply[fuel_supply[x][0]+1] = calc_fuel_supply[x][1]
    t = np.fromiter(dict_supply.keys(), dtype=float)
    fuel_demand = eval(demand_eq)
    if isinstance(fuel_demand, int):
        fuel_demand = fuel_demand*np.ones(len(t))
    for x in range(0, len(fuel_supply)):
        dict_demand[fuel_supply[x][0]] = fuel_demand[x]

    return dict_demand, dict_supply, dict_calc_demand, dict_calc_supply


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
    tables[0] = "timeseriessupply"+commod
    tables[2] = "timeseries"+commod+"calc_supply"
    tables[3] = "timeseriesdemand"+commod
    if demand_driven: 
        tables[1] = "timeseries"+commod+"calc_demand"
    else: 
        tables[1] = "timeseries"+commod+"calc_capacity"
    fuel_demand = cur.execute(
        "select time, sum(value) from "+tables[3]+" group by time").fetchall()
    fuel_supply = cur.execute(
        "select time, sum(value) from "+tables[0]+" group by time").fetchall()
    calc_fuel_demand = cur.execute(
        "select time, sum(value) from "+tables[1]+" group by time").fetchall()
    calc_fuel_supply = cur.execute(
        "select time, sum(value) from "+tables[2]+" group by time").fetchall()
    dict_demand = {}
    dict_supply = {}
    dict_calc_demand = {}
    dict_calc_supply = {}
    for x in range(0, len(fuel_supply)):
        dict_supply[fuel_supply[x][0]] = fuel_supply[x][1]
        dict_calc_demand[fuel_supply[x][0]+1] = calc_fuel_demand[x][1]
        dict_calc_supply[fuel_supply[x][0]+1] = calc_fuel_supply[x][1]

    t = np.fromiter(dict_supply.keys(), dtype=float)
    for x in range(0, len(t)):
        dict_demand[t[x]] = 0

    for x in range(0, len(fuel_supply)):
        for y in range(0, len(fuel_demand)):
            if fuel_demand[y][0] == fuel_supply[x][0]:
                dict_demand[fuel_supply[x][0]] = fuel_demand[y][1]

    return dict_demand, dict_supply, dict_calc_demand, dict_calc_supply



def residuals(dict_demand, dict_supply):
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

    start = int(list(dict_demand.keys())[0])
    demand_total = 0
    for x in range(start-1, len(dict_demand)):
        y = x+1
        demand_total += dict_demand[y]
    demand_mean = (1/len(dict_demand))*demand_total
    SStot = 0
    SSres = 0
    for x in range(start-1, len(dict_demand)):
        y = x+1
        SStot += (dict_demand[y]-demand_mean)**2
        SSres += (dict_demand[y]-dict_supply[y])**2

    Rsquared = 1-SSres / SStot
    return Rsquared


def chi_goodness_test(dict_demand, dict_supply):
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
    chi2 = 0
    start = int(list(dict_demand.keys())[0])
    for x in range(start-1, len(dict_demand)):
        y = x+1
        try:
            chi2 += (dict_supply[y]-dict_demand[y])**2 / dict_demand[y]
        except ZeroDivisionError:
            chi2 += 0

    return chi2


def supply_under_demand(dict_demand, dict_supply, demand_driven):
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
    num_negative = 0
    start = int(list(dict_demand.keys())[0])
    for x in range(start-1, len(dict_demand)):
        y = x+1
        if dict_supply[y] < dict_demand[y]:
            num_negative = num_negative + 1

    if demand_driven:
        number_under = num_negative
    else: 
        number_under = len(dict_demand) - num_negative
    return number_under 


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
