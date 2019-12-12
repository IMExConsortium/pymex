#!/usr/bin/python3
import os
import sys

pkg_dir = os.path.dirname( os.path.realpath(__file__) )
pylib_dir = os.path.join( pkg_dir, '..','pylib' )

if os.path.isdir( pylib_dir ):
    print("PROPY: using development library version")
    sys.path.insert(0,pylib_dir)

import argparse

from pymex.dipropy import Client


parser = argparse.ArgumentParser(description='MIF Reader')
parser.add_argument('--id',  dest="ident", type=str, required=True,
                   help='Identifier')
 
parser.add_argument('--operation',  dest="opcode", type=str, required=False,
                    help='Operation.', default="DEFAULT", choices=['getPubMed', 'getUprot', 'getRfseq'])

args = parser.parse_args()

ident = args.ident
opcode = args.opcode

if opcode in ['DEFAULT','getPubMed']:
    print("ProxyPy(getPubMed): " + ident)  
    DPC = DIPROClient()
    rec = DPC.getpubmed( ident  )
    print(rec)
    

    








