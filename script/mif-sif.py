#!/usr/bin/python3
import sys
import os

pkg_dir = os.path.dirname( os.path.realpath(__file__) )
pylib_dir = os.path.join( pkg_dir, '..','pylib' )

if os.path.isdir( pylib_dir ):
    print("mif-sif: using development library version")
    sys.path.insert(0,pylib_dir)

from zipfile import ZipFile

import argparse
import pymex.psimi as psimi

parser = argparse.ArgumentParser(description='MIF Reader')
parser.add_argument('--source-dir',  dest="sdir", type=str, required=True,
                    help='MIF file(s) directory. Compressed files OK.')

parser.add_argument('--acc',  dest="alist", nargs='*', type=str, required=True,
                    help='Accessions to test')
args = parser.parse_args()

mifParser = psimi.PsiMi254Parser()

# accession fileter list

alist = args.alist

files = []

for (dirpath, dirnames, filenames) in os.walk( args.sdir):
    for file in filenames:        
        fname = dirpath + '/' + file
        files.append( fname )
        
i = 0

mif = {}

for file in files:

    i = i + 1 
    aclist = {}
    source = []
    
    if file.find("unassigned") < 0:
        if file.endswith( ".zip" ):
            myzip = ZipFile( file, 'r' )

            for sl in myzip.namelist():
                if  sl.find("negative") < 0 :            
                    source.append( myzip.open( sl, 'r' ) )
        else:
            source.append( open(file, 'r' ) )
            
    if source:
        print( i, file )

        for cs in source:
            m = mifParser.parse( cs )
            ek0 = list(m["e10t"].keys())[0]
            pmid = m["e10t"][ek0]["pmid"]
            
            mif[pmid] = m
    
print("---- sif files starts here ----")

for pmid, cmif in mif.items():
    for iid, i11n in cmif["i11n"].items():
        plist= []
        llist = []
        for p11t in i11n["p11t"]:
            plist.append({"erole":p11t["erole"]["label"], "label":p11t["i10r"]["label"]})
            llist.append( p11t["i10r"]["label"] )

        # test if in accesion list

        keep = False

        for facc in alist:
            for pacc in llist:
                if facc == pacc:
                    keep = True
                    break

        if keep:

            # print out sif 

            if i11n["itype"]["label"] == "association":
            
                bait =""
                for p in plist:
                    if p["erole"] == "bait":
                        bait =  p["label"] 
                        break

                for p1 in plist:
                    if p1["label"] != bait:
                        if  p1["label"] > bait:
                            print( bait, ' pp ',  p1["label"] )
                        else:
                            print( p1["label"], ' pp ', bait )

            if i11n["itype"]["label"] == "physical association":
                for p1 in plist:
                    for p2 in plist:
                        if p1["label"] <  p2["label"]:
                            print( p1["label"], ' pp ',  p2["label"] )
                    
