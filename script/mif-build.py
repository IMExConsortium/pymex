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
parser = argparse.ArgumentParser( description='MIF Reader' )
parser.add_argument( '--source', '-s',  dest="source", type=str, required=False,
                     default = "data/builder-test-1.txt", 
                     help='File location (path or URL). Compressed file OK.')

#spyder hack: add '-i' option only if present (as added by spyder)
if '-i' in sys.argv:
    parser.add_argument( '-i',  dest="i", type=str, required=False, default=None) 
#spyder hack: DONE

args = parser.parse_args()

rb = pymex.mif254.RecordBuilder()

record = rb.build( args.source)

print( json.dumps(record,indent=2) )


