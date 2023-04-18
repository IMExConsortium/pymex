#!/usr/bin/python3
import sys
import os

pkg_dir = os.path.dirname( os.path.realpath(__file__) )
pylib_dir = os.path.join( pkg_dir, '..','pylib' )

if os.path.isdir( pylib_dir ):
    print("mif-digest: using source library version")
    sys.path.insert(0,pylib_dir)
    
import pymex
import argparse
import json

from lxml import etree as ET

import logging
logging.basicConfig(level=logging.WARN)     # needs logging configured

parser = argparse.ArgumentParser( description='UniprotKB Test' )

parser.add_argument('--upr', '-u', dest="upr", type=str,
                    required=False, default='P60010',
                    help='UniprotKB accession.')

args = parser.parse_args()

ucl = pymex.uprot.Record()
ucr = ucl.getRecord(args.upr)

#print(json.dumps(ucr.root,indent=1))
xref = ucr.xref

for x in xref:
    if 'Reactome' == x:
        rxrefl = xref[x] 
        for r in rxrefl:
            print(r)
