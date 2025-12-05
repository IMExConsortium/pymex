#!/usr/bin/python3
import sys
import os

pkg_dir = os.path.dirname( os.path.realpath(__file__) )
pylib_dir = os.path.join( pkg_dir, '..','pylib' )

if os.path.isdir( pylib_dir ):
    print("hgnc-digest: using source library version")
    sys.path.insert(0,pylib_dir)
    
import pymex
import argparse
import json

from lxml import etree as ET

import logging
logging.basicConfig(level=logging.WARN)     # needs logging configured

parser = argparse.ArgumentParser( description='InterPro Test' )

parser.add_argument('--taxid', dest="taxid", type=str,
                    required=False, default='4932',
                    help='NCBI Taxon ID.')

args = parser.parse_args()

utax = pymex.uprot.proteome.Record(debug=True)
rec = utax.getRecord(args.taxid, debug=True)

print(json.dumps(rec.root,indent=1))
sys.exit()
