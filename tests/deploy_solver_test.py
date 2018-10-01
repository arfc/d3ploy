import random
import sys
import os
dirname = os.path.dirname(os.path.abspath(__file__))
print(dirname)
dirname = dirname.split('/tests')[0]
dirname = dirname + '/d3ploy'
sys.path.append(dirname)
from no_inst import NOInst
from cyclus.agents import Institution, Agent
from cyclus import lib

# deploy_solver_fcn = NOInst.deploy_solver

for i in range(100):
    print('TRIAL ', i)
    diff = -1.0 * random.uniform(0.01, 30.0)
    commod = {}
    for i in range(4):
        commod.update({str(i): random.uniform(0.1, 9.9)})
    print(lib.Context)
    ctx = lib._Context
    obj = NOInst
    obj.commodity_dict = {'commod': commod}
    deploy_dict = obj.deploy_solver(obj, 'commod', diff)
    print(deploy_dict)
    # actually deploy and see if it's good
    final_diff = diff
    for key, val in deploy_dict.items():
        final_diff -= val * commod[key]
    
    if final_diff > min(commod.values()):
        raise ValueError('The difference after deployment exceeds the capacity of the smallest deployable prototype')
    else:
        print('GOOD JOB')
