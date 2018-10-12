import random
import copy
import math
from collections import defaultdict
import numpy as np
import scipy as sp

"""
This solver.py file contains auxillary functions that 
aid `no_inst.py'.
"""

def deploy_solver(commodity_dict, commod, diff):
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
    commod: str
        commodity driving deployment
    diff: float
        lack in supply

    Returns:
    --------
    deploy_dict: dict
        key: prototype name
        value: # to deploy
    """
    diff = -1.0 * diff
    proto_commod = commodity_dict[commod]
    min_cap = min(proto_commod.values())
    key_list = get_asc_key_list(proto_commod)

    remainder = diff
    deploy_dict = {}
    for proto in key_list:
        # if diff still smaller than the proto capacity,
        if remainder >= proto_commod[proto]:
            # get one
            deploy_dict[proto] = 1
            # see what the diff is now
            remainder -= proto_commod[proto]
            # if this is not enough, keep deploying until it's smaller than its cap
            while remainder > proto_commod[proto]:
                deploy_dict[proto] += 1
                remainder -= proto_commod[proto]

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
