#!/usr/bin/python3
import sys
import os

pkg_dir = os.path.dirname( os.path.realpath(__file__) )
pylib_dir = os.path.join( pkg_dir, '..','pylib' )

if os.path.isdir( pylib_dir ):
    print("icentral-test: using source library version")
    sys.path.insert(0,pylib_dir)
    
import pymex
import argparse
import json

from lxml import etree as ET

#import icclient

import zeep

import logging
logging.basicConfig(level=logging.WARN)     # needs logging configured

parser = argparse.ArgumentParser( description='ICentral Test' )

parser.add_argument('--operation', '-o', dest="operation", type=str,
                    required=False, default='status',
                    choices=['status', 'getrec', 'getall'],
                    help='Operation (default: status)')

parser.add_argument('--user-id', '-u', dest="uid", type=str,
                    required=False, default='',
                    help='User ID')

parser.add_argument('--user-pass', '-p', dest="passwd", type=str,
                    required=False, default='',
                    help='Password')

parser.add_argument('--imex-id', '-ii', dest="imexId", type=str,
                    required=False, default='IM-29799',
                    help='Imex Record Id.')

parser.add_argument('--status', '-s', dest="status", type=str,
                    required=False, default='',
                    help='Record Status.')

parser.add_argument('--first-rec', '-f', dest="frec", type=int,
                    required=False, default=0,
                    help='First record')

parser.add_argument('--max-rec', '-m', dest="mrec", type=int,
                    required=False, default=10,
                    help='Max records')

parser.add_argument('--linkout', '-l', dest="lfile", type=str,
                    required=False, default='',
                    help='LinkOut file')

args = parser.parse_args()

print( "IMex Id: ", args.imexId )

icc = pymex.icentral.ICentralClient( user = args.uid,
                                     password = args.passwd)

if args.operation =='status':
    res = icc.getServerStatus('')
    sys.exit()


if args.operation =='getall' and len(args.lfile) > 0:

    res = icc.getServerStatus('')

    (rlast,recl) = icc.getPubByStatus( status=args.status,
                                       firstrec=0,
                                       maxrec=1)
    print("Output file:",args.lfile)
    print("Total Records:",int(rlast))
    
    with open(args.lfile,"w") as loh:

        lwl= icc.lowrap().split('\n')
        for ln in lwl:
            if ln!='%%LINK-LIST%%':
                loh.write(ln)
                loh.write('\n')
            else:
                for frec in range(0,int(rlast),args.mrec):
                    print("Records:", frec, 'to', min(int(rlast),frec+args.mrec-1))
        
                    (rlast,recl) = icc.getPubByStatus( status=args.status,
                                                       firstrec=frec,
                                                       maxrec=args.mrec)

                    for r in recl:     
                        loh.write(icc.rec2linkout(r))
                        
    sys.exit()


if len(args.imexId) > 0:
    recl = icc.getPubById( ns='imex',
                          ac=args.imexId )

if len(args.status) > 0:
    recl = icc.getPubByStatus( status=args.status,
                              firstrec=args.frec,
                              maxrec=args.mrec)
    

if len(args.lfile) == 0:
    for r in recl:
        print(ET.tostring(r,pretty_print=True).decode())
    print("Total Records: ",len(recl))
    sys.exit()

if len(recl)>0:
    with open(args.lfile,"w") as loh:
        
        if len(recl) == 1:
            loh.write(icc.rec2linkout(recl[0]))
        else:
            lwl= icc.lowrap().split('\n')
            for ln in lwl:
                if ln!='%%LINK-LIST%%':
                    loh.write(ln)
                    loh.write('\n')
                else:
                    for r in recl:                        
                        loh.write(icc.rec2linkout(r))
        




    
