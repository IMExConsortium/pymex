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

parser.add_argument('--output', '-o', dest="ofile", type=str, 
                    required=False, default='STDOUT',
                    help='Output file [default: STDOUT].')

#spyder hack: add '-i' option only if present (as added by spyder)

if '-i' in sys.argv:
    parser.add_argument('-i',  dest="i", type=str,
                        required=False, default=None)

args = parser.parse_args()

ucl = pymex.uprot.Record()
ucr = ucl.getRecord(args.upr)

tmp = ucr.root["uniprot"]["entry"][0]

tmp= ucr.entry

if args.ofile == 'STDOUT':
    print( json.dumps(tmp,indent=1) )
else:
    with open(args.ofile,"w") as of:
        of.write( json.dumps(tmp,indent=1) )

        
print("Entry name: ", ucr.name['entry'])
        
#print( "Names: ", ucr.name )
#print( "\nComments:", ucr.comment.keys() )
#for k in ucr.comment:
#    print( " comments:",k," :: " , ucr.comment[k] )

#print( "\nFeatures:",list(ucr.feature.keys()))
#for k in ucr.feature:
#    print( " feature:",k," :: " , ucr.feature[k] )

#print( "\nXref:",list(ucr.xref.keys()))
#for k in ucr.xref:
#    print( " xref:",k," :: " , ucr.xref[k] )

#print( "Acc[primary]: ", ucr.accession['primary'] )
#print( "Acc[secondary]: ", ucr.accession['secondary'] )


    
