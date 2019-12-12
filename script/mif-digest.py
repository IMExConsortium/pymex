#!/usr/bin/python3
import sys
import os

pkg_dir = os.path.dirname( os.path.realpath(__file__) )
pylib_dir = os.path.join( pkg_dir, '..','pylib' )

if os.path.isdir( pylib_dir ):
    print("mif-digest: using development library version")
    sys.path.insert(0,pylib_dir)

import argparse
from zipfile import ZipFile
import pymex.psimi as psimi

# molecule cross reference list

xns=["pir","refseq","dip"]

parser = argparse.ArgumentParser(description='MIF Digest')
parser.add_argument('--source',  dest="source", type=str, required=True,
                   help='MIF file location (path or URL). Compressed file OK.')

parser.add_argument( '--mode',  dest="mode", type=str, required=False,
                     help='Default digest mode.' , default="DEFAULT", choices=['tab','gds'])

args = parser.parse_args()

MD = psimi.PsiMiDigest()

if  args.mode in ['DEFAULT','tab']:
    dig = MD.tabDigest( args.source ) 
    print( dig )

if  args.mode == 'gds' :
    dig = MD.dtsDigest( args.source ) 
    print( dig )

