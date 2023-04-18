#!/usr/bin/python3
import sys
import os

pkg_dir = os.path.dirname( os.path.realpath(__file__) )
pylib_dir = os.path.join( pkg_dir, '..','pylib' )

if os.path.isdir( pylib_dir ):
    print("hgncList2reactome: using source library version")
    sys.path.insert(0,pylib_dir)
    
import pymex
import argparse
import json

from lxml import etree as ET

import logging
logging.basicConfig(level=logging.WARN)     # needs logging configured

parser = argparse.ArgumentParser( description='hgncList2reactome' )

parser.add_argument('--hgncList', dest="hlst", type=str,
                    required=True, help='HGNC gene name list.')

args = parser.parse_args()


with open( args.hlst ,"r") as hlfh:
    for ln in hlfh:
        print( ln.strip() )

        hgnc = pymex.hgnc.HgncRecord()
        rec = hgnc.getRecord( ln.strip())
        print("  UniprotKB:",rec.uprAc)

        if rec.uprAc == None:            
            continue
        
        ucl = pymex.uprot.Record()
        ucr = ucl.getRecord(rec.uprAc)

        #print(json.dumps(ucr.root,indent=1))
        xref = ucr.xref

        for x in xref:
            if 'Reactome' == x:
                rxrefl = xref[x] 
                for r in rxrefl:
                    print("  Reactome:", r)

        sys.stdout.flush()

