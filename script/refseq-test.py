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

parser.add_argument('--db', dest="db", type=str,
                    required=False, default='nuccore',
                    help='NLM database (Default: nuccore).')

parser.add_argument('--debug', dest="debug", type=bool,
                    required=False, default=False,
                    help='Debug flag (Default: False).')

args = parser.parse_args()

rfsc = pymex.refseq.Record( debug=args.debug)
rec = rfsc.getRecord(args.rfsc, db=args.db)

#print(json.dumps(rec.root,indent=1))

print("Locus:",rec.locus)
print("PrimaryAc:",rec.primaryAc)

print(type(rec))
print("Sequence:",rec.sequence)

cdsfl =  rec.getFeatureLstByKey('CDS')
regsl =  rec.getFeatureLstByKey('Region')

for i in range(len(regsl)):
    print(i, regsl[i]['location'][0]['begin'],regsl[i]['location'][0]['end'], end=" ")

    for a in regsl[i]['attribute']:
        if a['name'] == 'region_name':
            print(a['value'])


    
if cdsfl is not None:
    for cds in cdsfl:
        print("CDS:", type(cds),cds)

        #alst = cds.attrs    
        #for a in alst:
        #    if a.name == 'translation':
        #        print("  ","Translation:",a.value)
