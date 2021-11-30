#!/usr/bin/python3
import os
import sys

pkg_dir = os.path.dirname( os.path.realpath(__file__) )
pylib_dir = os.path.join( pkg_dir, '..','pylib' )

if os.path.isdir( pylib_dir ):
    print("#uniprot-read: using source library version")
    sys.path.insert(0,pylib_dir)

import argparse
import json
from lxml import etree as ET
import pymex

import logging
logging.basicConfig(level=logging.WARN)     # needs logging configured

parser = argparse.ArgumentParser( description='UniprotKB Tool' )

parser.add_argument('--upa', '-u', dest="upa", type=str,
                    required=False, default='A8A1Q4',
                    help='Uniparc query.')

parser.add_argument('--mode', '-m', dest="mode", type=str,
                    required=False, default='get',
                    help='Mode.')

parser.add_argument('--output', '-o', dest="ofile", type=str, 
                    required=False, default='STDOUT',
                    help='Output file [default: STDOUT].')

#spyder hack: add '-i' option only if present (as added by spyder)

if '-i' in sys.argv:
    parser.add_argument('-i',  dest="i", type=str,
                        required=False, default=None)

args = parser.parse_args()

ucl = pymex.uparc.Record()
ucr = ucl.query(args.upa)

print(ET.tostring(ucr.recordTree,pretty_print=True).decode())
xxx
#tmp = ucr.root["uniprot"]["entry"][0]

tmp= ucr.entry

if args.ofile == 'STDOUT':
    print( json.dumps(tmp,indent=1) )
else:
    with open(args.ofile,"w") as of:
        of.write( json.dumps(tmp,indent=1) )

print(ucr.root["uniparc"]["entry"][0].keys())
print("Accession: ", ucr.accession)
print("Copyright: ", ucr.copyright)
print("Sequence: ", ucr.sequence)

for r in ucr.dbRef:
    if r["type"] == "UniProtKB/TrEMBL":
        print(r["id"],r["active"])
        for p in r["property"]:
            if p["type"] == "NCBI_taxonomy_id":
                print(p["value"])
                
for e in ucr.elist:
    print( e )
    print(e.accession)
    for r in e.dbRef:
        print(r)

