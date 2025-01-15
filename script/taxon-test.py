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

parser = argparse.ArgumentParser( description='UniprotKB Test' )

parser.add_argument('--taxid', dest="taxid", type=str,
                    required=False, default='9606',
                    help='TaxonID')

parser.add_argument('--debug', dest="debug", type=bool,
                    required=False, default=False,
                    help='Debug flag (Default: False).')

args = parser.parse_args()

taxdb = pymex.taxon.Record() # debug=args.debug)
rec = taxdb.getRecord(args.taxid)

if args.debug:
    print(json.dumps(rec.root,indent=1))
    pass

print("Lineage:",rec.lineage)
print("LineageRank:",rec.rank('phylum'))
print("Simple:",rec.lineageSimple)

print(type(rec))

