#!/usr/bin/python3
import os
import sys

pkg_dir = os.path.dirname( os.path.realpath(__file__) )
pylib_dir = os.path.join( pkg_dir, '..','pylib' )

if os.path.isdir( pylib_dir ):
    print("LEGPY: using development library version")
    sys.path.insert(0,pylib_dir)

import argparse

import io 
from zipfile import ZipFile
from lxml import etree as ET

import pymex.psimi
import pymex.dxf as DXF
import pymex.dippy as DP
import pymex.legpy as LP
import pymex.dipropy as DPX

parser = argparse.ArgumentParser(description='DIPPY Tool')
parser.add_argument( '--source',  dest="source", type=str, required=False,
                     help='MIF file location (path or URL). Compressed file OK.')

parser.add_argument( '--mode',  dest="mode", type=str, required=False,
                     help='Default  mode.' , default="DEFAULT", choices=['guest','admin'])

parser.add_argument( '--operation',  dest="opcode", type=str, required=False,
                     help='Default operation: status' , default="DEFAULT",
                     choices=['status','getlink','getnode','getsource','getexpt'])

parser.add_argument( '--trim',  dest="trim", type=str, required=False,
                     help='Trim mode (default: trim) ' , default="DEFAULT",
                     choices=['ixtrim','trim'])

parser.add_argument( '--ident',  dest="ident", type=str, required=False)

parser.add_argument( '--debug',  dest="debug", type=bool, required=False,
                     help='Debug flag (default: False)' , default=False,
                     choices=[True, False])

parser.add_argument( '--detail',  dest="detail", type=str, required=False,
                     help='Detail level (default: default)' , default="default",
                     choices=['default','base','stub','full','source'])


args = parser.parse_args()

opcode = 'status'

if  args.opcode in ['DEFAULT','status']:
    opcode = 'status'
else:
    opcode =  args.opcode

dpc = None # DP.Client()
lpc = LP.Client()

if opcode is not None:

    if opcode == 'status':
        lpc.getstatus()
        sys.exit(0)

if opcode in ['getnode']:

    print("LEGPY Tool(Get Node): " + args.ident)
    
    if args.ident is not None:
        (ns,ac) = args.ident.split(':')
    if ns == 'dip':
        rdts = lpc.getnode( ns=ns, ac = ac, detail=args.detail )
    
if opcode in ['getlink']:

    print("LEGPY Tool(Get Link): " + args.ident)
    
    if args.ident is not None:
        (ns,ac) = args.ident.split(':')
    if ns == 'dip':
        rdts = lpc.getlink( ns=ns, ac = ac, detail=args.detail )
        
if opcode in ['getsource']:

    print("LEGPY Tool(Get Source): " + args.ident)
    
    if args.ident is not None:
        (ns,ac) = args.ident.split(':')
    if ns == 'dip':
        rdts = lpc.getsource( ns=ns, ac = ac, detail=args.detail )
        
if opcode in ['getexpt']:

    print("LEGPY Tool(Get Experiment): " + args.ident)
    
    if args.ident is not None:
        (ns,ac) = args.ident.split(':')
    if ns == 'dip':
        rdts = lpc.getevid( ns=ns, ac = ac, detail=args.detail )        
        
if rdts is not None:
    print( ET.tostring(rdts,pretty_print=True).decode('UTF-8') )
    
            
