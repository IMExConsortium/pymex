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

parser.add_argument('--rfsc', dest="rfsc", type=str,
                    required=False, default='NM_019353.2',
                    help='RefSeq record id.')

args = parser.parse_args()

rfsc = pymex.refseq.Record()
rec = rfsc.getRecord(args.rfsc)

#print(json.dumps(rec.root,indent=1))

print("Locus:",rec.locus)
print("PrimaryAc:",rec.primaryAc)

print(type(rec))
print("Sequence:",rec.sequence)

cdsfl =  rec.getFeatureLstByKey('CDS')

if cdsfl is not None:
    for cds in cdsfl:
        print("CDS:", cds)
        alst = cds.attrs    
        for a in alst:
            if a.name == 'translation':
                print("  ","Translation:",a.value)
