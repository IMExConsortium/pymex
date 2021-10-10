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
                     default = "data/builder-test-1.tmif",
                     help='File location (path or URL). Compressed file OK.')

parser.add_argument( '--output', '-o', dest="ofile", type=str, required=False,
                     default='STDOUT',
                     help='Output file [default: STDOUT].')

parser.add_argument( '--output-format', '-of',  dest="oformat", type=str, required=False,
                     default='jmif', choices=['mif254', 'mif300','jmif'],
                     help='Output format [default: jmif].')

parser.add_argument( '--cvdef', '-c',  dest="cvpath", type=str, required=False,
                     default='',
                     help='Custom cv term definition file location.')

#spyder hack: add '-i' option only if present (as added by spyder)
if '-i' in sys.argv:
    parser.add_argument( '-i',  dest="i", type=str, required=False, default=None)
#spyder hack: DONE

args = parser.parse_args()

#input with test case is none
rb = pymex.mif.RecordBuilder( args.cvpath )

#input is the file name being passed in.
#output is the root datastructure; dictionary
record = rb.build( args.source)
print("oooooooff", args.cvpath)

if args.ofile == 'STDOUT':
    if args.oformat == 'mif254':
        #printing string rep of xml object directly with ET, toMif returns an element tree using the root datastructure.
        print( ET.tostring(record.toMif('mif254'),pretty_print=True).decode("utf-8") )
        print("testing print mif254")
    elif args.oformat == 'mif300':
        print( ET.tostring(record.toMif('mif300'),pretty_print=True).decode("utf-8") )
        print("testing print mif300")
    else:
        print( record.toJson() )
        print("testing just to JSON")
else:
    with open(args.ofile,"w") as of:
        if args.oformat == 'mif254':
            #writing an xml file from an ET object
            of.write( ET.tostring(record.toMif('mif254'),pretty_print=True).decode("utf-8") )
            print("test of.write 254")
        elif args.oformat == 'mif300':
            of.write( ET.tostring(record.toMif('mif300'),pretty_print=True).decode("utf-8") )
            print("test of.write 300")
        else:
            of.write( record.toJson() )
            print("test of.write toJSON")
