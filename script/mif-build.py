#!/usr/bin/python3
import sys
import os

pkg_dir = os.path.dirname( os.path.realpath(__file__) )
pylib_dir = os.path.join( pkg_dir, '..','pylib' )

if os.path.isdir( pylib_dir ):
    print("#mif-build: using source library version")
    sys.path.insert(0,pylib_dir)

import argparse
import pymex
import json
from lxml import etree as ET

parser = argparse.ArgumentParser( description='MIF Builder' )
parser.add_argument( '--source', '-s',  dest="source", type=str, required=False,
                     default = "data/builder-test-1.txt",
                     help='File location (path or URL). Compressed file OK.')

parser.add_argument( '--output', '-o', dest="ofile", type=str, required=False,
                     default='STDOUT',
                     help='Output file [default: STDOUT].')

parser.add_argument( '--output-format', '-of',  dest="oformat", type=str, required=False,
                     default='jmif', choices=['mif254', 'mif300','jmif'],
                     help='Output format [default: jmif].')

#spyder hack: add '-i' option only if present (as added by spyder)
if '-i' in sys.argv:
    parser.add_argument( '-i',  dest="i", type=str, required=False, default=None) 
#spyder hack: DONE

args = parser.parse_args()

rb = pymex.mif.RecordBuilder()

record = rb.build( args.source)

if args.ofile == 'STDOUT':
    if args.oformat == 'mif254':
        print( ET.tostring(record.toMif('mif254'),pretty_print=True).decode("utf-8") )
    elif args.oformat == 'mif300':
        print( ET.tostring(record.toMif('mif300'),pretty_print=True).decode("utf-8") )
    else:
        print( record.toJson() )
else:
    with open(args.ofile,"w") as of:
        if args.oformat == 'mif254':
            of.write( ET.tostring(record.toMif('mif254'),pretty_print=True).decode("utf-8") )
        elif args.oformat == 'mif300':
            of.write( ET.tostring(record.toMif('mif300'),pretty_print=True).decode("utf-8") )
        else:
            of.write( record.toJson() )




