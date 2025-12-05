#!/usr/bin/python3
import sys
import os
import gzip
import time

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

parser.add_argument('--taxid-list', '-txl', dest="taxidlist", type=str,
                    required=False, default='',
                    help='TaxonID list')

parser.add_argument('--taxid-column', '-txc', dest="tcol", type=int,
                    required=False, default=2,
                    help='TaxonID column')

parser.add_argument('--output-dir', '-od', dest="odir", type=str,
                    required=False, default='',
                    help='output directory')

parser.add_argument('--debug', dest="debug", type=bool,
                    required=False, default=False,
                    help='Debug flag (Default: False).')

parser.add_argument('--api-key', '-k', dest="key", type=str,
                    required=False, default='e4016fa76d8be09479a689f27f69ed9fb308',
                    help='NCBI API key')

parser.add_argument('--api-delay', '-d', dest="delay", type=float,
                    required=False, default='0.1',
                    help='NCBI API delay')


args = parser.parse_args()



if len(args.taxidlist) == 0:
    txl = [args.taxid]
else:

    print("Taxon list:", args.taxidlist)

    txl = []
    if args.taxidlist.endswith(".gz"):
        txh = gzip.open(args.taxidlist,"r")
    else:
        txh = open(args.taxidlist,"r")

    for ln in txh:        
        cols = str(ln.decode()).strip().split( "\t" )
        if cols[0] != 'Proteome Id':
            txl.append(cols[args.tcol])
    txh.close()


print("Output dir: ", args.odir)
for tx in txl:
    if args.debug:
        print("TaxID:",tx)
    
    if len(args.odir) > 0 and os.path.exists(args.odir+"/"+tx+".json"):
        if args.debug:
            print("Skipping: ", args.odir+"/"+tx+".json")
        continue

    taxdb = pymex.taxon.Record(key=args.key, retry=3) # debug=args.debug)
    rec = taxdb.getRecord(tx)

    if args.debug:
        print(json.dumps(rec.root,indent=1))
    

    if len(args.odir) > 0:
        if args.debug:
            print("Writing:", args.odir+"/"+tx+'.json')
        with open( args.odir+"/"+tx+'.json', "w" ) as oh:
            oh.write(json.dumps(rec.root,indent=1)+"\n")
            
    else:
        print("Lineage:",rec.lineage)
        print("LineageRank:",rec.rank('phylum'))
        print("Simple:",rec.lineageSimple)

    if args.debug:
        time.sleep(1*args.delay)
    else:    
        time.sleep(args.delay)
