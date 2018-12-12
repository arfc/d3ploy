""" This python file contains tech pref capability tests for TimeSeriesInst
archetype. 
"""

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
import d3ploy.tester as functions

from nose.tools import assert_in, assert_true, assert_equals

# Delete previously generated files
direc = os.listdir('./')
hit_list = glob.glob('*.sqlite') + glob.glob('*.json') + glob.glob('*.png')
for file in hit_list:
    os.remove(file)

ENV = dict(os.environ)
ENV['PYTHONPATH'] = ".:" + ENV.get('PYTHONPATH', '')


def test_constraint_deploy():
    output_ = 'test_constraint_deploy.sqlite'
    input_path = os.path.abspath(__file__)
    find = 'd3ploy/'
    indx = input_path.rfind('d3ploy/')
    input_ = input_path.replace(input_path[indx+len(find):], 'input/test_transition.xml')
    s = subprocess.check_output(['cyclus', '-o', output_, input_],
                                universal_newlines=True, env=ENV)
    cur = functions.get_cursor(output_)
    reactor2_entry = cur.execute('SELECT entertime FROM agententry WHERE ' +
                                 'prototype == "reactor2"').fetchall()
    time_after_constraint = cur.execute('SELECT time FROM timeseriessupplystorageuox ' +
                                        'WHERE value > 8000').fetchone()[0]
    for row in reactor2_entry:
        assert (row['entertime'] >= time_after_constraint + 1)
