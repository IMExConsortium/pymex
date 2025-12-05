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

parser.add_argument('--upmatch', dest="ipum", type=str,
                    required=False, default='A0A000',
                    help='UniprotKB accession.')

parser.add_argument('--interpro', dest="ipro", type=str,
                    required=False, default='IPR015422',
                    help='Interpro accession.')

parser.add_argument('--ip-mirror','-ipm', dest="ipmirror", type=str,
                    required=False, default='',
                    help='Record location.')

args = parser.parse_args()

if len(args.ipmirror) > 0:
    ipum = pymex.interpro.upmatch.Record(debug=True,mirror_xml=args.ipmirror)
else:
    ipum = pymex.interpro.upmatch.Record(debug=True)


print("Path:", ipum.getfpath(args.ipum) )

    
rec = ipum.getRecord(args.ipum)

print(json.dumps(rec.root,indent=1))
sys.exit()

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
