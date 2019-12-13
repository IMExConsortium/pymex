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

import pymex

#test_mif25='/cluster1/mirrors/imex/intact/psi25/2018/9171338.zip'
test_mif25='ftp://ftp.ebi.ac.uk/pub/databases/intact/current/psi25/pmid/2019/15138291.xml'

parser = argparse.ArgumentParser(description='MIF Reader')
parser.add_argument( '--source',  dest="source", type=str, required=True,
                     help='MIF file location (path or URL). Compressed file OK.')
args = parser.parse_args()

mifParser = pymex.psimi.Mif254Parser()

source = []

if args.source.endswith( ".zip" ):
    myzip = ZipFile( args.source, 'r' )

    for sl in myzip.namelist():
        print(sl)
        
        # skip 'negative' interaction files
        # ( ie experiments demonstrating interaction does not happen) 
        
        if  sl.find("negative") < 0 :            
            source.append( myzip.open( sl, 'r' ) )
else:
    source.append( open(args.source, 'r' ) )

aclist = {}
s = {} 

for cs in source:    
    rec = mifParser.parse( cs )

    for int in rec.inlist:
        
        print( " =======" )        
        
        itype  = int.type
        
        method = "N/S"
        if int.evlist is not None and len(int.evlist) > 0:
           intmethod = int.evlist[0]['intMth']
                      
           print( "\n Interaction:  label:\t",int.label,"\timexId:\t", int.imex  )
           print( "  Interaction Type: ",itype["ac"],"\t",itype["label"])
           print( "  Method(interaction): ",intmethod["ac"],"\t",intmethod["label"])
           if 'prtMth' in int.evlist[0]:
               prtmethod = int.evlist[0]['prtMth']
               if prtmethod is not None:
                   print( "  Id Mth(participant): ",prtmethod["ac"],"\t",prtmethod["label"])

           if int.ptolist is not None and len(int.ptolist) > 0:
               print( " Participants:" )
               for pto in int.ptolist:
                   print( pto )
                   #print( "  ------" )
                   #print( "  ",pto.interactor.pxref["ac"],"\t", pto.interactor.label,pto.interactor.name )
                   #print( "     type: ", pto.interactor.type["label"] )
                   #print( "     role: ", pto.erole[0]["label"] )
                   #print( "  ------" ) 

    print( " =======" )


