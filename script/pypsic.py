#!/usr/bin/python3
import os
import sys

# get script location
pkg_dir = os.path.dirname( os.path.realpath(__file__) )

# add library location (if present)
pylib_dir = os.path.join( pkg_dir, '..','pylib' )
if os.path.isdir( pylib_dir ):
    print("#PYPSIC: using source library version")
    sys.path.insert( 0, pylib_dir )

import argparse
import pymex

parser = argparse.ArgumentParser(description='PSICQUC Client')

parser.add_argument('--server',  dest="server", type=str, required=False,
                    help='Default PSICQUIC server', default='imex' )

parser.add_argument('--service',  dest="service", type=str, required=False,
                    help='Service.', default="DEFAULT",
                    choices=[ 'DEFAULT', 'list',
                              'interactor', 'interaction', 'query'] )
parser.add_argument( '--query',  dest="query", type=str, required=False,
                     help='Query.', default="P60010")

parser.add_argument('--first',  dest="first", type=int, required=False,
                    help='First record.', default=1 )

parser.add_argument('--max',  dest="max", type=int, required=False,
                    help='Max number of records.', default=50 )


parser.add_argument('--format',  dest="format", type=str, required=False,
                    help='Result format.', default="xml25", choices=['xml25', 'tab25', 'dxf15'] )

args = parser.parse_args()

server = args.server
service = args.service
query = args.query

res = None

if service in ['DEFAULT','list']:
    DPC = pymex.pypsic.Client()
    print( DPC.registry )

if service in ['interactor']:
    print("#PyPsic(interactor): " + ident )  
    DPC = pymex.pypsic.Client()
    res = DPC.getinteractor( ident, server=server,
                             first=args.first, max=args.max,
                             format=args.format )

if service in ['interaction']:
    print("#PyPsic(interaction): " + ident )
    DPC = pymex.pypsic.Client()
    res = DPC.getinteraction( ident, server=server,
                              first=args.first, max=args.max,
                              format=args.format)
                
if service in ['query']:
    print("#PsicPy(query): " + query )
    DPC = pymex.pypsic.Client()
    res = DPC.getquery( query, server=server,
                        first=args.first, max=args.max,
                        format=args.format)

if res is not None:
    print( res )
    
