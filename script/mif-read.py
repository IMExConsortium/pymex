#!/usr/bin/python3
import sys
import os

pkg_dir = os.path.dirname( os.path.realpath(__file__) )
pylib_dir = os.path.join( pkg_dir, '..','pylib' )

if os.path.isdir( pylib_dir ):
    print("mif-digest: using source library version")
    sys.path.insert(0,pylib_dir)

import argparse
from urllib.request import urlopen
from io import BytesIO
from zipfile import ZipFile

import pymex

#test_mif25='/cluster1/mirrors/imex/intact/psi25/2018/9171338.zip'
test_mif25='ftp://ftp.ebi.ac.uk/pub/databases/intact/current/psi25/pmid/2019/15138291.zip'

parser = argparse.ArgumentParser( description='MIF Reader' )
parser.add_argument( '--source',  dest="source", type=str, required=False,
                     default = test_mif25, 
                     help='MIF file location (path or URL). Compressed file OK.')

parser.add_argument( '--format',  dest="format", type=str, required=False,
                     default='mif254', choices=['mif254', 'mif300'],
                     help='Input file format.')

args = parser.parse_args()

if args.format in['mif254']:
    mifParser = pymex.mif254.Mif254Parser()

if args.format in['mif300']:
    mifParser = pymex.mid300.Mif300Parser()
    
source = []

if args.source.endswith( ".zip" ):

    myzip = ZipFile( BytesIO( urlopen( args.source ).read() ) )

    for sl in myzip.namelist():
        print(sl)
        
        # skip 'negative' interaction files
        # ( ie experiments demonstrating interaction does not happen) 
        
        if  sl.find("negative") < 0 :            
            source.append( myzip.open( sl, 'r' ) )
else:
    source.append( urlopen( args.source ) )

aclist = {}
s = {} 

for cs in source:    
    rec = mifParser.parse( cs )
    print(type(rec))
    print(rec.toJson())

