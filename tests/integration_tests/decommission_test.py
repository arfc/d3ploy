""" This python file contains decommission capability tests for TimeSeriesInst
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
hit_list = glob.glob('*.sqlite') + glob.glob('*.json') + glob.glob('*.png') +glob.glob('*.txt')
for file in hit_list:
    os.remove(file)

ENV = dict(os.environ)
ENV['PYTHONPATH'] = ".:" + ENV.get('PYTHONPATH', '')


def test_decommission():
    output_ = 'POWER.txt'
    input_path = os.path.abspath(__file__)
    find = 'd3ploy/'
    indx = input_path.rfind('d3ploy/')
    input_ = input_path.replace(
        input_path[indx + len(find):], 'input/decommission.xml')
    s = subprocess.check_output(['cyclus', input_],
                                universal_newlines=True, env=ENV)
    with open('POWER.txt') as f:
        lines = f.readlines()
    f.close()
    val = float(lines[-1].split(' ')[5])
    assert (val < 50.)
    os.remove('POWER.txt')

def test_backdecom():
    output_ = 'POWER.txt'
    input_path = os.path.abspath(__file__)
    find = 'd3ploy/'
    indx = input_path.rfind('d3ploy/')
    input_ = input_path.replace(
        input_path[indx + len(find):], 'input/backdecom.xml')
    s = subprocess.check_output(['cyclus', input_],
                                universal_newlines=True, env=ENV)
    with open('fuel.txt') as f:
        lines = f.readlines()
    f.close()
    val = float(lines[-1].split(' ')[5])
    assert (val < 50.)
    os.remove('POWER.txt')
    os.remove('fuel.txt')
