#!/usr/bin/python3
import sys
import os

pkg_dir = os.path.dirname( os.path.realpath(__file__) )
pylib_dir = os.path.join( pkg_dir, '..','pylib' )

if os.path.isdir( pylib_dir ):
    print("DIPPY: using development library version")
    sys.path.insert(0,pylib_dir)

import argparse
import io 

from zipfile import ZipFile
from lxml import etree as ET

import pymex.psimi as psimi
import pymex.dxf as DXF
import pymex.dippy as DP
import pymex.dipropy as DPX

parser = argparse.ArgumentParser(description='DIPPY Tool')
parser.add_argument( '--mif',  dest="mif", type=str, required=False,
                     help='MIF file location (path or URL). Compressed file OK.')

parser.add_argument( '--dxf',  dest="dxf", type=str, required=False,
                     help='DXF file location (path or URL).')

parser.add_argument( '--mode',  dest="mode", type=str, required=False,
                     help='Default  mode.' , default="DEFAULT", choices=['guest','admin'])

parser.add_argument( '--operation',  dest="opcode", type=str, required=False,
                     help='Default operation: status' , default="DEFAULT",
                     choices=['status','getnode','addnode',
                              'addtaxon',
                              'getsrce','addsrce',
                              'getexpt','addexpt',
                              'getevid','addevid',
                              'getedge','addedge',
                              'getimex','addimex'])

parser.add_argument( '--trim',  dest="trim", type=str, required=False,
                     help='Trim mode (default: trim) ' , default="DEFAULT",
                     choices=['ixtrim','trim'])

parser.add_argument( '--auto-create',  dest="acf", type=str, required=False,
                     default="DEFAULT", choices=['True','False'],
                     help='Auto-create subrecords (eg source and nodes for experiemnts).' )

parser.add_argument( '--ident',  dest="ident", type=str, required=False,
                     help='Record dentifier. <ns::accession> format')

parser.add_argument( '--debug','-d',  dest="debug", type=bool, required=False,
                     help='Debug flag (default: False)' , default=False,
                     choices=[True, False])

args = parser.parse_args()

opcode = 'status'

if  args.opcode in ['DEFAULT','status']:
    opcode = 'status'
else:
    opcode =  args.opcode

dpc = DP.Client()

#dpc = pymex.dippy.Client()

if opcode is not None:
    if opcode == 'status':
        dpc.getstatus()
        sys.exit(0)


if opcode in ['getsrce','getimex']:   
    if args.ident is not None:

        (ns,ac) = args.ident.split('::')

        if ns not in  ['dip','imex']:
             print("DIPPY Tool: " + ns + " :unknown source identifier type")
             sys.exit(1)
             
        if opcode in ['getsrce']:
            res = dpc.getsource( ns=ns, ac = ac )             

        if opcode in ['getimex']:
            res = dpc.getimex( ns=ns, ac = ac, format='mif254' )             
                
        if res is not None:
            print( res )
            
if args.mif is None and args.dxf is None and args.ident is None:
    print("DIPPY Tool: no input")
    sys.exit(1)


# identifier input
#-----------------

if args.ident is not None:
    (ns,ac) = args.ident.split('::')

    if opcode in ['addsrce'] and ns in ['pubmed']:
        
        print("DIPPY Tool(Add Source): " + args.ident)                 
        DPC = DPX.Client()
        rec = DPC.getpubmed( ac )
        rec = rec.replace('dxf14','dxf15')
        rec = rec.replace( '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>','')

        if args.debug:
            print(rec)
            
        dxf15parse = ET.XMLParser( remove_blank_text=True )
        dom = ET.parse( io.StringIO(rec), dxf15parse )        
        dpc.addsource( dom, mode='source' )
        sys.exit(0)
        
    if opcode in ['getsrce']  and ns in ['dip','imex','pubmed']:
        res = dpc.getsource( ns=ns, ac = ac )
        print(res)
        sys.exit(0)

    if opcode in ['getexpt']  and ns in ['dip','imex']:
        res = dpc.getexpt( ns=ns, ac = ac )
        print(res)        
        sys.exit(0)

    if opcode in ['getevid']  and ns in ['dip']:
        res = dpc.getevid( ns=ns, ac = ac )
        print(res)        
        sys.exit(0)

    if opcode in ['getnode']  and ns in ['dip','refseq','uniprot']:
        res = dpc.getnode( ns=ns, ac = ac )
        print(res)
        res = res.replace("<?xml version='1.0' encoding='UTF-8'?>",'')
        ip = DXF.DXF15Parser()
        irec = ip.parse( io.StringIO(res) )
        if len(ip.dxf) > 0:
            for n in ip.dxf:
                print(n)
    
        
        sys.exit(0)

    if opcode in ['getedge']  and ns in ['dip']:
        res = dpc.getedge( ns=ns, ac = ac )
        print(res)        
        sys.exit(0)
        
        #print("DIPPY Tool: " + ns + " :unknown source identifier type")
        #sys.exit(1)
        

# dxf file input
#---------------

if args.dxf is not None:
    print("DIPPY Tool: DXF input file: " + args.dxf)

    dxfile = []
    
    if args.dxf.endswith( ".zip" ):
        myzip = ZipFile( args.dxf, 'r' )

        for sl in myzip.namelist():
            if  sl.find("negative") < 0 :
                dxfile.append( myzip.open( sl, 'r' ) )
    else:
        dxfile.append( open( args.dxf, 'r' ) )
        
    if len( dxfile ) > 0:
        for s in dxfile:            
            dxf15parse = ET.XMLParser( remove_blank_text=True )
            doc = ET.parse( s, dxf15parse )
            if opcode == 'addexpt':

                if args.acf in ['DEFAULT','True']: 
                    print("Auto-create mode")
                    dpa = DP.ExptSubmitter()                    
                    dpa.addExpt( doc )                    
                    
                else:
                    res = dpc.addexpt( doc, mode='experiment' )
                    print(res)
                next;    
            if opcode == 'addevid':
                res = dpc.addexpt( doc, mode='evidence' )
                print(res)
            if opcode == 'addedge':

                if args.acf in ['DEFAULT','True']: 
                    print("Auto-create mode")
                    esub = DP.EdgeSubmitter()                    
                    esub.addEdge( doc )
                else:    
                    res = dpc.addedge( doc, mode='edge' )
                #print(res)
                next;
                
            if opcode == 'addnode':
                if args.acf in ['DEFAULT','True']: 
                    print("Auto-create mode")
                    nsub = DP.NodeSubmitter()                    
                    nsub.addNode( doc )
                else:
                    res = dpc.addnode( doc, mode='node' )
                print(res.text)
            if opcode == 'addtaxon':
                res = dpc.addnode( doc, mode='taxon' )
                print(res)
            
            
    sys.exit(0)
    

# mif file input
#---------------
    
if args.mif is not None:
    print("DIPPY Tool: MIF input file: " + args.mif)

    mifile = []
    
    if args.mif.endswith( ".zip" ):
        myzip = ZipFile( args.mif, 'r' )

        for sl in myzip.namelist():
        
            # skip 'negative' interaction files
            # ( ie experiments demonstrating interaction does not happen)
        
            if  sl.find("negative") < 0 :
                mifile.append( myzip.open( sl, 'r' ) )
    else:
        mifile.append( open( args.mif, 'r' ) )

    if len( mifile ) > 0:

        mifParser = psimi.Mif254Parser()         
        rec = mifParser.parse( mifile[0] )
        PMC = psimi.PsiMiConvert( rec )
    
        if args.trim == 'ixtrim':
            irlist = PMC.ixtrim()
        else:
            irlist = PMC.ixuntrim()
            
        if opcode in ['addnode','addtaxon']:           
            for ir in irlist:
                print(ir)       

                if ir.type['ac'] in ['MI:0326','MI:0327']:
                    
                    # interactor -> protein/peptide
                    
                    prot = dpc.prot2dxf( ir )
            
                    dts = dpc.dxf.datasetType()
                    dts.node.append(prot)
            
                    if opcode == 'addnode':
                        # add to imxdip
                        res = dpc.addnode( dts, mode='node' )
                        print(res)        
        
                    if opcode == 'addtaxon':            
                        # add to imxdip
                        res = dpc.addnode( dts, mode='taxon' )
                        print(res)        
        
        if opcode in ['addexpt']:
            for intn in rec.inlist:
                print(intn)
                print("\nParticipants\n")
                
                for p in intn.ptolist:
                    print("\n  find\n")
                    print(p)

                print("\nEvidence\n")
                                        
                for e in intn.evolist:
                    print("\n  find\n") 
                    print(e)

        if opcode in ['addedge']:
            for intn in rec.inlist:
                print(intn.mif25)

                
        if opcode in ['addimex']:
            (ns,ac) = args.ident.split('::')

            print("Adding IMEX record for ns/ac: " + ns + "/" + ac) 
            dpc.addimex(ns=ns,ac=ac,record = "abcd...")
            sys.exit(0)
            
        for intn in rec.inlist:
            if opcode == 'addfoo':

                print("\nINTERACTION\n-----------")
                print(intn)        

                # add to imxdip
                res = dpc.addexpt( intn, mode='experiment' )
                if res:
                    text = res.replace( "<?xml version='1.0' encoding='UTF-8'?>", "")
                    dxfns = { 'dxf': 'http://dip.doe-mbi.ucla.edu/services/dxf15' }           

                    tree = ET.fromstring(text)
                    dset = tree.xpath('//dxf:dataset',namespaces = dxfns )
                    if dset:
                        print(ET.tostring(dset[0],pretty_print=True).decode('utf-8'))
                                                                
            
