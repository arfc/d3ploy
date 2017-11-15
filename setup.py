#!/usr/bin/env python
from distutils.core import setup


VERSION = '0.0.1'
setup_kwargs = {
    "version": VERSION,
    "description": 'Demand Driven Archetypes',
    "author": 'Robert Flanagan',
    }

if __name__ == '__main__':
    setup(
        name='d3ploy',
        packages=['d3ploy'],
        scripts=['xo'],
        **setup_kwargs
        )
