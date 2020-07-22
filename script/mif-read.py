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

test_mif25='ftp://ftp.ebi.ac.uk/pub/databases/intact/current/psi25/pmid/2020/7984244.zip'

print(sys.argv)

parser = argparse.ArgumentParser( description='MIF Reader' )
parser.add_argument( '--source', '-s',  dest="source", type=str, required=False,
                     default = test_mif25, 
                     help='File location (path or URL). Compressed file OK.')

parser.add_argument( '--input-format', '-if',  dest="format", type=str, required=False,
                     default='mif254', choices=['mif254', 'mif300','jmif'],
                     help='Input file format [default: mif254].')

parser.add_argument( '--output-format', '-of',  dest="oformat", type=str, required=False,
                     default='jmif', choices=['mif254', 'mif300','jmif'],
                     help='Output format [default: jmif].')

parser.add_argument( '--output', '-o', dest="ofile", type=str, required=False,
                     default='STDOUT',
                     help='Output file [default: STDOUT].')

#spyder hack: add '-i' option only if present (as added by spyder)

if '-i' in sys.argv:
    parser.add_argument( '-i',  dest="i", type=str, required=False, default=None) 

args = parser.parse_args()

if args.format in['mif254']:
    mifParser = pymex.mif254.Mif254Parser()

if args.format in['mif300']:
    mifParser = pymex.mif300.Mif300Parser()
    
source = []

if args.source.endswith( ".zip" ):

    myzip = ZipFile( BytesIO( urlopen( args.source ).read() ) )

    for sl in myzip.namelist():
        print(sl)
        
        # skip 'negative' interaction files
        # ( ie experiments demonstrating interaction does not happen) 
        
        if  sl.find("negative") < 0 :            
            source.append( myzip.open( sl, 'r' ) )

elif ( args.source.startswith( "http://" ) or
       args.source.startswith( "https://" ) or
       args.source.startswith( "ftp://" ) ):
    
    source.append( urlopen( args.source ) )
else:
    source.append( open( args.source,'r' ) )

aclist = {}
s = {} 

for cs in source:

    if args.format == 'jmif':        
        rec = pymex.mif254.Mif254Record().fromJson(cs) 
    else:    
        rec = mifParser.parse( cs )
            
    if args.ofile == 'STDOUT':
         if args.oformat == 'mif254':
             print( rec.toMif254() )
         else:
             print( rec.toJson() )
    else:
        with open(args.ofile,"w") as of:
            if args.oformat == 'mif254':
                of.write( rec.toMif254() )
            else:
                of.write( rec.toJson() )
