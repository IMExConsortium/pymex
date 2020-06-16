import os
import sys
sys.path.insert( 0, os.path.dirname(os.path.realpath(__file__)) )
pkg_dir = os.path.dirname( os.path.realpath(__file__) )
version_file = open(os.path.join( pkg_dir, 'VERSION') )
version = version_file.read().strip()

import psimi

import dipropy

import dippy
import legpy

import pypsic
import pycent

import pylout
