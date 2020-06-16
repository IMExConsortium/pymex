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
                    help='User name', default='' )

parser.add_argument('--password',  dest='password', type=str, required=False,
                    help='Password', default='' )

parser.add_argument('--debug',  dest="debug", type=bool, required=False,
                    help='Debug.', default=False )

args = parser.parse_args()

res = None

PCC = pymex.pycent.Client( user=args.user, password=args.password,
                           server=args.server, debug=args.debug )


query = "RELEASED"

first = 1
max = 100

 
res = PCC.queryPublication( query=query, firstRec=first, max=10 )

total = res['lastRec']

print("Total: " + str(total) )

linkout = pymex.pylout.LOutRecordList()


while first + max < total:
    res = PCC.queryPublication( query=query, firstRec=first, max=max )

    print( "First: " + str( first ) )

    publist = res['publicationList']['publication']

    for pub in publist:
        print( pub['status'] )

        if 'RELEASED' in pub['status']:
            print('   ###: ' + pub['imexAccession'], end ='\t' )
            imex = pub['imexAccession']
            pmid = None
            
            try:                            
                for id in  pub['identifier']:                
                    if id['ns'] == 'pmid':
                        print ('   pubmed:' + id['ac'], end='\t' )
                        pmid = id['ac']
            except:
                print( '   identifier: ' + str( pub['identifier'] ), end ='\t' )

            print( '   owner: ' + pub['owner'], end='\t' )
                    
                    
            try:        
                groups = pub['adminGroupList']['group']
                for group in groups:
                    if group in ['DIP','INTACT','MINT','MPIDB','UNIPROT']:
                        print('   curated by: ' + group, end=' ' )
                
            except:
                print( " groups: ",  str(pub['adminGroupList']), end='' )
                
            

            if pmid is not None and imex != 'N/A':
                linkout.appendLink( imex, imex, pmid )
                print('')
            else:
                print("   record skipped... ")
                
    first = first + max 
    #break

print( linkout.toXML().decode() )
