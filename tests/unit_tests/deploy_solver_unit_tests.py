import random
import sys
import os
import pytest
import d3ploy.solver as solver


def test_min_deploy_solver():
    """ Tests if the minimize_number_of_deployment function works correctly
        by deploying the smallest number of facilities while meeting diff"""
    for i in range(100):
        diff = -1.0 * random.uniform(0.01, 30.0)
        commod = {}
        for i in range(4):
            commod.update({str(i): random.uniform(0.1, 9.9)})
        deploy_dict = solver.deploy_solver(commodity_dict={'commod': commod},
                                           pref_dict={},
                                           commod='commod',
                                           diff=diff,
                                           time=1)
        # actually deploy and see if it's good
        final_diff = diff
        for key, val in deploy_dict.items():
            final_diff += val * commod[key]
        
        if final_diff > min(commod.values()):
            raise ValueError(
                'The difference after deployment exceeds the capacity of the smallest deployable prototype')
        # if it didn't raise valueerror, we are good
        assert(True)

def test_pref_solver_const():
    """ Tests if the preference_deploy function works correctly
        for constant preference values
        by deploying only the most preferred prototype to meet diff """
    for i in range(100):
        diff = -1.0 * random.uniform(0.01, 30.0)
        commod = {}
        pref_dict = {}
        for i in range(3):
            commod.update({str(i): random.uniform(0.1, 9.9)})
            pref_dict.update({str(i): random.uniform(0.1, 9.9)})
        deploy_dict = solver.deploy_solver(commodity_dict={'commod': commod},
                                           pref_dict={'commod':pref_dict},
                                           commod='commod',
                                           diff=diff,
                                           time=1)
        # check if only one prototype is deployed
        assert (len(deploy_dict.keys()) == 1)

        # get highest preference value prototype
        most_preferred_proto = max(pref_dict, key=pref_dict.get)
        # check if the deployed proto is the most preferred prototype
        for proto, deploy_num in deploy_dict.items():
            assert (proto == most_preferred_proto)
            # check if deployed capacity is the right value
            deployed_cap = deploy_num * commod[proto]
            if deployed_cap < diff:
                raise ValueError('Underdeploys')
            elif (deployed_cap + diff) > commod[proto]:
                raise ValueError('Overdeploys') 
    assert(True)


def test_pref_solver_eq():
    """ Tests if the preference_deploy function works correctly
        when the preference values are given as an equation """
    diff = -10
    commod = {'1': 2,
              '2': 4}
    pref_dict = {'1': '1*t',
                 '2': '10 - (1*t)'}
    for t in range(10):
        print(t)
        deploy_dict = solver.deploy_solver(commodity_dict={'commod': commod},
                                            pref_dict={'commod': pref_dict},
                                            commod='commod',
                                            diff=diff,
                                            time=t)
        if t < 5:
            assert(deploy_dict['2'] == 3)
        if t == 5:
            assert(deploy_dict['2'] == 2)
            assert(deploy_dict['1'] == 1)
        if t > 5:
            assert(deploy_dict['1'] == 5)
    assert(True)
