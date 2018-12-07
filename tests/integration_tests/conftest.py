import json
import re
import subprocess
import os
import sqlite3 as lite
import pytest
import copy
import glob
import sys
from nose.tools import assert_in, assert_true, assert_equals

calc_methods = ["ma", "arma", "arch", "poly",
                "exp_smoothing", "holt_winters", "fft"]

def pytest_generate_tests(metafunc):
    if 'calc_method' in metafunc.fixturenames:
        metafunc.parametrize('calc_method', calc_methods) 
