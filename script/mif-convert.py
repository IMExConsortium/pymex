#!/usr/bin/python3
import sys
import os

pkg_dir = os.path.dirname( os.path.realpath(__file__) )
pylib_dir = os.path.join( pkg_dir, '..','pylib' )

if os.path.isdir( pylib_dir ):
    print("mif-convert: using development library version")
    sys.path.insert(0,pylib_dir)

import argparse
from zipfile import ZipFile

import pymex

parser = argparse.ArgumentParser(description='MIF Convert')
parser.add_argument('--source',  dest="source", type=str, required=True,
                   help='MIF file location (path or URL). Compressed file OK.')

parser.add_argument( '--mode',  dest="mode", type=str, required=False,
                     help='conversion mode.' , default="null")

parser.add_argument( '--single',  dest="single", type=str, required=False,
                     help='Only single item output.' , default="Y", choices=["Y","N"])

parser.add_argument( '--format',  dest="format", type=str, required=False,
                     help='Only single item output.' ,
                     default="DEFAULT", choices=["repr","mif254","list",'dxf15'])

parser.add_argument( '--intid',  dest="intid", type=str, required=False,
                     help='Interaction id.', default = None)

args = parser.parse_args()

intid = args.intid

source = []
if args.source.endswith( ".zip" ):
    myzip = ZipFile( args.source, 'r' )

    for sl in myzip.namelist():
        
        # skip 'negative' interaction files
        # ( ie experiments demonstrating interaction does not happen)
        
        if  sl.find("negative") < 0 :
            source.append( myzip.open( sl, 'r' ) )
else:
    source.append( open( args.source, 'r' ) )
    
if len(source) > 0:
 
    mb = pymex.psimi.Mif254Builder()
    dxb = pymex.psimi.Dxf15Builder()

    print("Mode: " + args.mode)
    if intid is not None:
        print("Interaction: " + intid)
    
    mifParser = pymex.psimi.Mif254Parser()         
    rec = mifParser.parse( source[0] )
    PMC = pymex.psimi.PsiMiConvert( rec )
    mb.addSource(rec.seo)
    inl = None
    
    if args.mode == 'trimall' :
        inl = PMC.ixtrim()
        inl = PMC.trim()
        
    if args.mode == 'trim' :
        inl = PMC.trim()
                
    if args.mode == 'untrim' :
        PMC.trim()
        inl = PMC.untrim()        
        
    if args.mode == 'ixtrim' :
        inl = PMC.ixtrim()
        
    if args.mode == 'ixuntrim' :
        PMC.ixtrim()
        inl = PMC.ixuntrim()
                       
    if args.mode == 'matrix' :
        inl = PMC.matrix(intid)         

    if args.mode == 'spoke' :
        inl = PMC.spoke() 
        
    if inl is not None:        
        if isinstance( inl, pymex.psimi.record.Record ):            
            if args.format == 'DEFAULT':
                print( inl )
            if args.format == 'repr':
                print( repr(inl) )
                
            if args.format == 'mif254':
                mb.buildRecord(inl)
                print( mb.docStr )
        else:
            for i in inl:
                if intid is not None and i.label != intid:
                    continue
            
                if args.format == 'DEFAULT':
                    print( i )
                    print()

                if args.format == 'repr':
                    print( repr(i) )
                    print()

                if args.format == 'list':
                    if isinstance( i,  psimi.interaction.Interaction):
                        print( i.label +"\t" + str(len(i.ptlist)) + "/" + str(len(i.ptall)))
                    else:
                        print( i.label )
                
                if args.format == 'mif254':
                
                    if isinstance( i, psimi.interactor.Interactor):                
                        mb.addInteractor( mb.irlst, i )

                    if isinstance( i, psimi.interaction.Interaction):                
                        mb.addInteraction( mb.inlst, i )
                    
                    if isinstance( i, psimi.evidence.Evidence):                
                        mb.addEvidence( mb.etlst, i )

                    if isinstance( i, psimi.experiment.Experiment):                
                        mb.addEvidence( mb.etlst, i )
                                        
                    print( mb.docStr)
                    print()


                if args.format == 'dxf15':
                     
                    if isinstance( i, psimi.interaction.Interaction):                
                        dxb.addInteraction( dxb.inlst, i )
                        
                    print( dxb.docStr)
                    print()
                                        
                        
                if args.single == 'Y':                
                    break
            
