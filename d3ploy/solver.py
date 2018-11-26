import random
import copy
import math
from collections import defaultdict
import numpy as np

"""
This solver.py file contains auxillary functions that
aid `timeseries_inst.py'.
"""


def deploy_solver(commodity_dict, pref_dict, commod, diff, time):
    """ This function optimizes prototypes to deploy to minimize over
        deployment of prototypes.
    Paramters:
    ----------
    commodity_dict: dictionary
        key: str
            commodity name
        value: dictionary
            key: str
                prototype name
            value: float
                prototype capacity
    pref_dict: dictionary
        key: str
            commodity name
        value: dictionary
            key: str
                prototype name
            value: str
                preference as an equation
    commod: str
        commodity driving deployment
    diff: float
        lack in supply
    time: int
        time of evaluation

    Returns:
    --------
    deploy_dict: dict
        key: prototype name
        value: # to deploy
    """
    diff = -1.0 * diff
    proto_commod = commodity_dict[commod]
    # if the preference is defined
    if commod in pref_dict.keys():
        pref_fac = pref_dict[commod]
        # evalute the preference functions
        # at the current time
        t = time
        eval_pref_fac = {}
        for facility, preference_eq in pref_fac.items():
            eval_pref_fac[facility] = eval(str(preference_eq))
        # check if the preference values are different
        if len(set(eval_pref_fac.values())) != 1:
            # if there is a difference,
            # deploy the one with highest preference
            # until it oversupplies
            return preference_deploy(proto_commod, eval_pref_fac, diff)

    # if preference is not given,
    # or all the preference values are the same,
    # deploy to minimize number of deployment
    return minimize_number_of_deployment(proto_commod, diff)


def preference_deploy(proto_commod, pref_fac, diff):
    """ This function deploys the facility with the highest preference only.
    Paramters:
    ----------
    proto_commod: dictionary
        key: prototype name
        value: prototype capacity
    pref_fac: dictionary
        key: prototype name
        value: preference value
    diff: float
        amount of capacity that is needed

    Returns:
    --------
    deploy_dict: dictionary
        key: prototype name
        value: number of prototype to deploy
    """
    # get the facility with highest preference
    deploy_dict = {}
    proto = get_asc_key_list(pref_fac)[0]
    remainder = diff

    if remainder >= proto_commod[proto]:
        deploy_dict[proto] = 1
        remainder -= proto_commod[proto]
        while remainder > proto_commod[proto]:
            deploy_dict[proto] += 1
            remainder -= proto_commod[proto]
        if remainder == 0:
            return deploy_dict
        else:
            deploy_dict[proto] += 1
    elif remainder > 0:
        deploy_dict[proto] = 1
    
    return deploy_dict


def minimize_number_of_deployment(proto_commod, remainder):
    """ This function deploys facilities to meet the lack in
    capacity by deploying the least number of facilities.

    Paramters:
    ----------
    proto_commod: dictionary
        key: prototype name
        value: prototype capacity
    remainder: float
        amount of capacity that is needed

    Returns:
    --------
    deploy_dict: dictionary
        key: prototype name
        value: number of prototype to deploy
    """
    deploy_dict = {}
    min_cap = min(proto_commod.values())
    key_list = get_asc_key_list(proto_commod)
    for proto in key_list:
        # if diff still smaller than the proto capacity,
        if remainder >= proto_commod[proto]:
            deploy_dict[proto] = 1
            remainder -= proto_commod[proto]
            while remainder > proto_commod[proto]:
                deploy_dict[proto] += 1
                remainder -= proto_commod[proto]
    if remainder == 0:
        return deploy_dict

    for proto in list(reversed(key_list)):
        # see if the prototype cap is bigger than remainder
        if remainder > proto_commod[proto]:
            continue
        if proto in deploy_dict.keys():
            deploy_dict[proto] += 1
        else:
            deploy_dict[proto] = 1
        break

    return deploy_dict


def get_asc_key_list(dicti):
    """ This function sorts keys in ascending order
        of their values

    Parameters:
    -----------
    dictionary: dict
        key: key
        value: value to be sorted

    Returns:
    --------
    key_list: list
        list of keys in ascending order of values
    """
    key_list = [' '] * len(dicti.values())
    sorted_caps = sorted(dicti.values(), reverse=True)
    for key, val in dicti.items():
        indx = sorted_caps.index(val)
        key_list[indx] = key
    return key_list
