#!/usr/bin/python3
import sys
import os

pkg_dir = os.path.dirname( os.path.realpath(__file__) )
pylib_dir = os.path.join( pkg_dir, '..','pylib' )

if os.path.isdir( pylib_dir ):
    print("mif-digest: using source library version")
    sys.path.insert(0,pylib_dir)


import argparse
from urllib.request import urlopen
from io import BytesIO
from zipfile import ZipFile

from lxml import etree as ET

import pymex

#test_mif25 = 'ftp://ftp.ebi.ac.uk/pub/databases/intact/current/psi25/pmid/2019/15138291.zip'
#test_mif25 = 'ftp://ftp.ebi.ac.uk/pub/databases/intact/current/psi25/pmid/2018/27571176.zip'

#test_mif25 = 'data/mif254/27571176-expand-mif254.xml'
test_mif25 = 'data/mif254/15138291-compact-mif254.xml'

parser = argparse.ArgumentParser( description='MIF Reader' )
parser.add_argument('--source', '-s',  dest="source", type=str,
                    required=False, default = test_mif25,
                    help='File location (path or URL). Compressed file OK.')

parser.add_argument('--input-format', '-if',  dest="format", type=str,
                    required=False, default='mif254',
                    choices=['mif254', 'mif300','jmif'],
                    help='Input file format [default: mif254].')

parser.add_argument('--output-format', '-of',  dest="oformat", type=str,
                    required=False, default='jmif',
                    choices=['mif254', 'mif300','jmif'],
                    help='Output format [default: jmif].')

#this is a location to write a new file.
parser.add_argument('--output', '-o', dest="ofile", type=str,
                    required=False, default='STDOUT',
                    help='Output file [default: STDOUT].')

#spyder hack: add '-i' option only if present (as added by spyder)

if '-i' in sys.argv:
    parser.add_argument('-i',  dest="i", type=str,
                        required=False, default=None)

args = parser.parse_args()

source = []

if args.source.endswith( ".zip" ):

    myzip = ZipFile( BytesIO( urlopen( args.source ).read() ) )

    for sl in myzip.namelist():
        print(sl)

        # skip 'negative' interaction files
        # ( ie experiments demonstrating interaction does not happen)

        if  sl.find("negative") < 0 :
            source.append( myzip.open( sl, 'r' ) )

elif ( args.source.startswith( "http://" ) or
       args.source.startswith( "https://" ) or
       args.source.startswith( "ftp://" ) ):

    source.append( urlopen( args.source ) )
else:
    source.append( open( args.source,'r' ) )

aclist = {}
s = {}

#source is the string corresponding to file path.
for cs in source:

#input-format arg (if) tells it how to parse to passed in file.
    if args.format == 'jmif':
        rec = pymex.mif.Record().parseJson(cs)
    else:
        rec = pymex.mif.Record().parseMif(cs, ver=args.format )
        print("parsing MIF")

#default just prints the xml rep of the chosen output-format (of) format
#if ofile is specified, it actually writes the xml to the specified location.
#default of is just jmif, which prints the json rep of the root structure.
    if args.ofile == 'STDOUT':
         if args.oformat == 'mif254':
             #print("debug type:")
             #print(type(rec.toXml('mif254')))
             print( ET.tostring(rec.toMif('mif254'),
                                pretty_print=True).decode("utf-8") )
         elif args.oformat == 'mif300':
             print( ET.tostring(rec.toMif('mif300'),
                                pretty_print=True).decode("utf-8") )
         else:
             print( rec.toJson() )
             print('its def this')
         print("just maing sure")
    else:
        with open(args.ofile,"w") as of:
            if args.oformat == 'mif254':
                of.write( ET.tostring(rec.toXml('mif254'),
                                      pretty_print=True).decode("utf-8") )
            elif args.oformat == 'mif300':
                of.write( ET.tostring(rec.toXml('mif300'),
                                      pretty_print=True).decode("utf-8") )
            else:
                of.write( rec.toJson() )
