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

parser.add_argument('--hgnc', dest="hgnc", type=str,
                    required=False, default='ZNF3',
                    help='HGNC gene name.')

args = parser.parse_args()

hgnc = pymex.hgnc.HgncRecord()
rec = hgnc.getRecord(args.hgnc)

print(json.dumps(rec.root,indent=1))

print("Symbol:",rec.symbol)
print("Entrez:",rec.entrezId)
print("OMIM:",rec.omimId)
print("UniprotKB:",rec.uprAc)
