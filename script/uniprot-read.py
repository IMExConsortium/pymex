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

parser.add_argument('--upr', '-u', dest="upr", type=str,
                    required=False, default='P60010',
                    help='UniprotKB accession.')

parser.add_argument('--mode', '-m', dest="mode", type=str,
                    required=False, default='get',
                    help='Mode.')

#spyder hack: add '-i' option only if present (as added by spyder)

if '-i' in sys.argv:
    parser.add_argument('-i',  dest="i", type=str,
                        required=False, default=None)

args = parser.parse_args()

ucl = pymex.up.UniRecord()
ucr = ucl.getRecord(args.upr)

#print(type(ucr.root))

tmp = ucr.root["uniprot"]["entry"][0]

tmp= ucr.entry

print(json.dumps(tmp,indent=1))
