import random
import sys
import os
import pytest
dirname = os.path.dirname(os.path.abspath(__file__))
print(dirname)
dirname = dirname.split('/tests')[0]
dirname = dirname + '/d3ploy'
sys.path.append(dirname)
import solver

# deploy_solver_fcn = NOInst.deploy_solver


def test_deploy_solver():
    for i in range(100):
        diff = -1.0 * random.uniform(0.01, 30.0)
        commod = {}
        for i in range(4):
            commod.update({str(i): random.uniform(0.1, 9.9)})
        commodity_dict = {'commod': commod}
        deploy_dict = solver.deploy_solver(commodity_dict, 'commod', diff)
        # actually deploy and see if it's good
        final_diff = diff
        print(commodity_dict)
        for key, val in deploy_dict.items():
            final_diff += val * commod[key]

        print(final_diff)
        print(deploy_dict)
        if final_diff > min(commod.values()):
            raise ValueError('The difference after deployment exceeds the capacity of the smallest deployable prototype')
        
        # if it didn't raise valueerror, we are good
        assert(True)
