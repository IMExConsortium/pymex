#!/usr/bin/python3
import os
import sys

# get script location
pkg_dir = os.path.dirname( os.path.realpath(__file__) )

# add library location (if present)
pylib_dir = os.path.join( pkg_dir, '..','pylib' )
if os.path.isdir( pylib_dir ):
    print("#PYCENT: using source library version")
    sys.path.insert( 0, pylib_dir )

import argparse
import pymex

parser = argparse.ArgumentParser(description='ICENTRAL Client')

parser.add_argument('--server',  dest='server', type=str, required=False,
                    help='Default ICENTRAL server', default='DEFAULT',
                    choices = ['DEFAULT','prod','beta','test', 'dev'])

parser.add_argument('--user', dest='user', type=str, required=False,
                    help='User name', default='lukasz' )

parser.add_argument('--password',  dest='password', type=str, required=False,
                    help='Password', default='444ls$$$LS' )

parser.add_argument('--service',  dest="service", type=str, required=False,
                    help='Service', default="DEFAULT",
                    choices=[ 'DEFAULT', 'status', 'aquery', 'pquery'] )

parser.add_argument( '--query',  dest="query", type=str, required=False,
                     help='Query.', default="P60010")

parser.add_argument('--first',  dest="first", type=int, required=False,
                    help='First record.', default=1 )

parser.add_argument('--max',  dest="max", type=int, required=False,
                    help='Max number of records.', default=50 )

parser.add_argument('--debug',  dest="debug", type=bool, required=False,
                    help='Debug.', default=False )

parser.add_argument('--format',  dest="format", type=str, required=False,
                    help='Result format.', default="xml25", choices=['xml25', 'tab25', 'dxf15'] )

args = parser.parse_args()

server = args.server
service = args.service
query = args.query

res = None

PCC = pymex.pycent.Client( user=args.user, password=args.password,
                           server=args.server, debug=args.debug )

if service in [ 'DEFAULT', 'status' ]:
    print( "#PyCent(status)" )
    print( PCC.getstatus() )

if service in [ 'pquery' ]:
    print("#PyCent(publication query): " + query )  
    res = PCC.queryPublication( query=query, firstRec=args.first, max=args.max )

if service in [ 'aquery' ]:
    print("#PyCent(attachment query): " + query )  
    res = PCC.queryAttachment( query=query, firstRec=args.first, max=args.max )

if service in [ 'interaction' ]:
    print("#PyCent(interaction): " + ident )
    PCC = pymex.pycent.Client()
    res = PCC.getinteraction( ident, server=server,
                              first=args.first, max=args.max,
                              format=args.format)
    
if res is not None:
    print( res )
    
