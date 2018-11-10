import random
import sys
import os
import pytest
import d3ploy.solver as solver


def test_deploy_solver():
    for i in range(100):
        diff = -1.0 * random.uniform(0.01, 30.0)
        commod = {}
        for i in range(4):
            commod.update({str(i): random.uniform(0.1, 9.9)})
        deploy_dict = solver.deploy_solver({'commod':commod}, 'commod', diff)
        # actually deploy and see if it's good
        final_diff = diff
        for key, val in deploy_dict.items():
            final_diff += val * commod[key]

        if final_diff > min(commod.values()):
            raise ValueError('The difference after deployment exceeds the capacity of the smallest deployable prototype')
        
        # if it didn't raise valueerror, we are good
        assert(True)
