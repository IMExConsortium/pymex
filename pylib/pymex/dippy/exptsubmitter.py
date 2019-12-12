import sys
sys.path.insert(0,"/cluster1/home/lukasz/git/psi-mi-tools/pylib")
sys.path.insert(0,"/cluster1/home/lukasz/git/dip-backend/pylib")
sys.path.insert(0,"/cluster1/home/lukasz/git/dip-proxy-tools/pylib")

import re
import io
import dippy as DP
import dipropy as DPX
import psimi
from lxml import etree as ET

class ExptSubmitter():
    def __init__( self, user='guest', password='guest',
                  mode='dev', debug=False ):

        self.dxfns = { 'dxf': 'http://dip.doe-mbi.ucla.edu/services/dxf15' }
        self.dpc = DP.Client()
        self.nsub = DP.NodeSubmitter()
        self.ssub = DP.SrceSubmitter()
        
    def addExpt(self, doc):
        print(type(doc))
        if isinstance( doc, ET._ElementTree):
            return self.addDxfExpt(doc)
        
        if isinstance( doc, psimi.Interaction):
            return self.addPsimiExpt( doc )        

        stype = str(type(doc))

        #if isinstance( doc, 'zeep.objects.nodeType'):
        if stype == "<class 'zeep.objects.nodeType'>":
            #dts = self.dxf.datasetType( [node])
            return self.addZeepExpt( doc )

    def addPsimiExpt(self, expt):
        print("psimi")
        return None

    def addDxfExpt(self, expt):
        print("dxf")
        dxfExpt = self.dpc.dom2dts( expt)

        if len( dxfExpt.node ) != 1:
            print("ERROR: Multiple nodes passed.")
            return None

        return self.addZeepExpt( dxfExpt.node[0] )
        
    def addZeepExpt( self, expt ):        
        if expt.type.ac not in ['dxf:0063', 'dip:309']:  
            print("ERROR: Not an experiment node.") 
            return None
        
        intList = expt.partList.part
        for i in intList:
            print("Part AC: " + i.node.ac)
            #print(type(i.node))
            pin =  self.nsub.addNode(i.node)
            #print(type(pi))
            i.node = pin     

        # get source

        imexRec = None
        imexSrc = None
        
        pmidSrc = None
        
        dipSrc = None
        
        dipSrcRec = None
        sdts = None
        
        for x in expt['xrefList']['xref']:  
            if x['type'] == 'described-by':
                if x['ns'] == 'dip':
                    dipSrc = x['ac']
                if x['ns'].lower() == 'pubmed':
                    pmidSrc = x['ac']
            if x['type'] == 'identical-to':
                if x['ns'] == 'imex':
                    imexRec = x['ac']
                    if imexRec is not None and len(imexRec) > 0:
                        imexSrc = re.sub('-[0-9]+$','',imexRec)
                        if imexSrc.startswith("IM-") :
                            print("IMEX Record: " + imexRec)
                            print("IMEX Source: " + imexSrc)
                        else:
                            imexSrc = None
                            imexRec = None
                    else:
                        imexSrc = None
                        imexRec = None

        # imex source 
                        
        if imexSrc is not None:
            print("IMEx Source: " + imexSrc)
            dsres =  self.dpc.getsource( ns='imex', ac=imexSrc )
            dsdxp = DP.DXF15Parser()
            dsdxp.parse(dsres.text)
            
            # src dataset
            sdts = self.dpc.dom2dts(dsdxp.dom)
            if sdts is not None:
                print( "Found imex source match: " +                       
                       sdts['node'][0]['ac'] )                       

                dipSrcRec = sdts['node'][0]['ac']

        # legacy dip source 
                        
        if sdts is None and dipSrc is not None:
            print("DIP Source: " + dipSrc)
            dsres =  self.dpc.getsource( ns='dip', ac=dipSrc )
            dsdxp = DP.DXF15Parser()
            dsdxp.parse(dsres.text)
            
            # src dataset
            sdts = self.dpc.dom2dts( dsdxp.dom )
            if sdts is not None:
                print( "Found dip source match: " +                       
                       sdts['node'][0]['ac'] )                       

                dipSrcRec = sdts['node'][0]['ac']
                        
        # pmid source (no legacy info and/or no legacy present)
                    
        if sdts is None and pmidSrc is not None:
            print("PubMed Source " + pmidSrc)
            dsres =  self.dpc.getsource( ns='pubmed', ac=pmidSrc )
            dsdxp = DP.DXF15Parser()
            dsdxp.parse(dsres.text)
            
            # src dataset
            sdts = self.dpc.dom2dts(dsdxp.dom)
            if sdts is not None:
                print( "Found pubmed source match: " +                       
                       sdts['node'][0]['ac'] )
                dipSrcRec = sdts['node'][0]['ac']

        # still no record found
                    
        if sdts is None and pmidSrc is not None:

            # fetch record from pubmed 
            print("Fetching from pubmed...")    
            DPC = DPX.Client()
            prec = DPC.getpubmed( pmidSrc )
            prec = prec.replace('dxf14','dxf15')
            prec = re.sub( r'<\?.+\?>','',prec)
                        
            dxf15parse = ET.XMLParser( remove_blank_text=True )
            dom = ET.parse( io.StringIO(prec), dxf15parse )               
            sres = self.dpc.addsource( dom, mode='source' )
            
            dsdxp = DP.DXF15Parser()
            dsdxp.parse( sres.text )
                
            # src dataset
            sdts = self.dpc.dom2dts(dsdxp.dom)
            if sdts is not None:
                print( "Created DIP source record: " +                       
                       sdts['node'][0]['ac'] )
                dipSrcRec = sdts['node'][0]['ac']

        if sdts is not None:
            # add imex source xref (when needed)

            imexMiss = True
            pxlst = sdts['node'][0]['xrefList']['xref']
            
            for x in pxlst:
                print(x['type'] +":"+ x['ac'])
                if x['type'] == "identical-to" and x['ns'] == 'imex':
                    if imexSrc is None and len(x['ac']) > 0:
                        print("WARNING: IMEX id conflict!!!")
                    if imexSrc is not None and imexSrc == x['ac']:
                        imexMatch = False
                        print( "OK: IMEX id match!!!" )
                        
            if imexMiss and imexSrc is not None and len(imexSrc) > 0:
                print("Adding Source IMEx ID: " + str(imexSrc))
                ixRef = self.dpc.dxf.xrefType( typeNs="dxf", typeAc="dxf:0009",
                                               type="identical-to",                                        
                                               ns="imex",
                                               ac=imexSrc)
                sdts['node'][0].xrefList.xref.append(ixRef)
                
                sres = self.dpc.addsource( sdts, mode='source' )
                dsdxp = DP.DXF15Parser()
                dsdxp.parse( sres.text )
                
                # src dataset
                sdts = self.dpc.dom2dts(dsdxp.dom)
                if sdts is not None:                
                    dipSrcRec = sdts['node'][0]['ac']
                
        if( dipSrcRec is not None):
            if dipSrc is None:                        
                print("DIP Source record (unknown legacy or new): " + dipSrcRec)

                sxRef = self.dpc.dxf.xrefType( typeNs="dxf", typeAc="dxf:0014",
                                               type="described-by",                                        
                                               ns="dip",
                                               ac=dipSrcRec)
                
                expt.xrefList.xref.append(sxRef) 
            
            else:
                print("DIP Source record (known legacy): " + dipSrcRec)
                      
        # test if experiments already present
        exptDip = None

        if expt['ns'] == 'dip':
            exptDip = expt['ac']

        print("Experiment ID: "  + exptDip)
                
        if dipSrcRec is not None:
            xres = self.dpc.addexpt( expt )
            exdxp = DP.DXF15Parser()
            exdxp.parse( xres.text )
            xdts = self.dpc.dom2dts( exdxp.dom )
            return xdts
        
        return None

    def getnodeident(self, xlist, sanitize = True ):

        upt = None
        rfs = None
        gid = None
        for x in xlist:
            if x['type'] == 'identical-to':
                if x['ns'] == "uniprotkb":
                    upt = x['ac']

                    if sanitize:
                        # sanitize uniprot (drop version/isoform)
                        upt = re.sub('(-[0-9]+)?(\.[0-9]+)?','', upt)                     
                        x['ac'] = upt
                                                        
                if x['ns'] == "refseq":                            
                    rfs = x['ac']

                    if sanitize:
                        # sanitize refseq (drop version)
                        rfs =  re.sub('\.[0-9]+','', rfs) 
                        x['ac'] = rfs
                            
                if x['ns'] == "entrezgene":
                    gid = x['ac']

        return (upt,rfs,gid)
