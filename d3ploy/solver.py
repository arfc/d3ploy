import random
import copy
import math
from collections import defaultdict
from collections import OrderedDict
import numpy as np

"""
This solver.py file contains auxillary functions that
aid `timeseries_inst.py'.
"""


def deploy_solver(commodity_supply, commodity_dict, commod, diff, time):
    """ This function optimizes prototypes to deploy to minimize over
        deployment of prototypes.
    Paramters:
    ----------
    comomdity_supply: dictionary
        key: commod
        value: dictionary
            key: time
            value: amount of supply of commod at time
    commodity_dict: dictionary
        key: str
            commodity name
        value: dictionary
            key: str
                prototype name
            value: float
                prototype capacity
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

    eval_pref_fac = {}
    for proto, val_dict in proto_commod.items():
        # evalute the preference functions
        # at the current time
        t = time
        pref = eval(val_dict['pref'])
        eval_pref_fac[proto] = pref

    for proto, val_dict in proto_commod.items():
        if val_dict['second_commod'] != '0':
            current_supply = commodity_supply[val_dict['second_commod']][time]
            if current_supply < float(val_dict['constraint']):
                eval_pref_fac[proto] = -1

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
        value: dictionary
            key: 'cap', 'pref', 'second_commod', 'constraint'
            value
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
    proto = sorted(pref_fac, key=pref_fac.get, reverse=True)[0]
    if diff >= proto_commod[proto]['cap']:
        deploy_dict[proto] = 1
        diff -= proto_commod[proto]['cap']
        while diff > proto_commod[proto]['cap']:
            deploy_dict[proto] += 1
            diff -= proto_commod[proto]['cap']
        if diff == 0:
            return deploy_dict
        else:
            deploy_dict[proto] += 1
    elif diff > 0:
        deploy_dict[proto] = 1
    return deploy_dict


def minimize_number_of_deployment(proto_commod, remainder):
    """ This function deploys facilities to meet the lack in
    capacity by deploying the least number of facilities.

    Parameters:
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
    cap_dict = {}
    for proto, val_dict in proto_commod.items():
        cap_dict[proto] = val_dict['cap']
    min_cap = min(cap_dict.values())
    key_list = sorted(cap_dict, key=cap_dict.get, reverse=True)
    for proto in key_list:
        # if diff still smaller than the proto capacity,
        if remainder >= proto_commod[proto]['cap']:
            deploy_dict[proto] = 1
            remainder -= proto_commod[proto]['cap']
            while remainder > proto_commod[proto]['cap']:
                deploy_dict[proto] += 1
                remainder -= proto_commod[proto]['cap']
    if remainder == 0:
        return deploy_dict

    for proto in list(reversed(key_list)):
        # see if the prototype cap is bigger than remainder
        if remainder > proto_commod[proto]['cap']:
            continue
        if proto in deploy_dict.keys():
            deploy_dict[proto] += 1
        else:
            deploy_dict[proto] = 1
        break

    return deploy_dict
