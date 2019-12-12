import sys
#sys.path.insert(0,"/cluster1/home/lukasz/git/psi-mi-tools/pylib")
#sys.path.insert(0,"/cluster1/home/lukasz/git/dip-backend/pylib")
#sys.path.insert(0,"/cluster1/home/lukasz/git/dip-proxy-tools/pylib")

import re
import io
import json

import dxf as DXF
import dippy as DP
import dipropy as DPX

import psimi
from lxml import etree as ET

class SrceSubmitter():
    def __init__( self, user='guest', password='guest',
                  mode='dev', debug=False ):

        self.dxfns = { 'dxf': 'http://dip.doe-mbi.ucla.edu/services/dxf15' }
        self.dpc = DP.Client()
        
    def addSrce(self, doc):
        print("NsrceSubmitter.addSrce:" + str(type(doc)))
                
        if isinstance( doc, ET._ElementTree):
            return self.addDxfSrce(doc)
        
        if isinstance( doc, psimi.Interactor):
            return self.addPsimiSrce( doc )        

        stype = str(type(doc))
        
        #if isinstance( doc, 'zeep.objects.nodeType'):
        if stype == "<class 'zeep.objects.nodeType'>":
            #dts = self.dxf.datasetType( [node])
            return self.addZeepSrce( doc )

        #if isinstance( doc, 'zeep.objects.datasetType'):
        if stype == "<class 'zeep.objects.datasetType'>":
            if len(doc.node) == 1:
                return self.addZeepSrce( doc.node[0] )
            
    def addPsimiSrce(self, doc):
        print("add psimi source")
        # convert mif -> dxf -> zeep
        # call addDxfSrce
        return None
    
    def addDxfSrce(self, doc ):
        print("add dxf source")
        dxfNode = self.dpc.dom2dts( doc )
        return self.addZeepSrce( dxfNode )

    def addZeepSrce(self, srce ):
        print("add/upate zeep source")



        
        if node.type.name not in ['protein','peptide']:
            print("ERROR: Not protein/peptide node.") 
            return None

        ndipID = None
        
        if len(node.ns) > 0 and len(node.ac) > 0:
            ndipID  = node.ac
            print("Node ID: " + node.ns + ":" + node.ac)
        else:
            for x in node.xrefList.xref:                
                if x.type == 'identical-to' and x.ns == 'dip':
                    ndipID = x.ac
            if ndipID is not None:
                print("Node DIP ID (by xref): " + ndipID)
            else:
                print("Node DIP ID: N/A")
                
        if ndipID is not None:            
            # known: get node from dip
            res =  self.dpc.getnode( ns='dip', ac=ndipID )
            if res.status_code == 200:
                odoc = res.text
            else:                    
                sys.exit(1)
                    
            dxp = DXF.DXF15Parser()
            dxp.parse(odoc)
                
            # node dataset
            ndts = self.dpc.dom2dts(dxp.dom)                
            if ndts is not None:
                # known node
                print(" Known node:" + ndts.node[0].ac)
                return  ndts.node[0]
            
            else:
                # legacy/unknown node: add
                print(" Legacy(unknown) node: " + ndipID)
                #print(inode)

                (upt,rfs,gid) = self.getNodeIdent(node.xrefList.xref)
                print((upt,rfs,gid)
                )   
                # look for uniprot/refseq/genid
                    
                if upt is not None and len(upt) > 0:
                    print(upt)
                    unode = self.dpc.getdxfnode( ns='uniprotkb', ac=upt )
                    #print(unode)
                    #print("XXXXXX")
                    if unode is not None:
                        print(" Uniprot match: " + unode['ac'])
                        if  ndipID != unode['ac']:
                            print( " Node ID not unique (legacy): " + ndipID  
                                   + " (database):" + unode['ac'])
                            node['ac'] = unode['ac']
                                
                if rfs is not None and len(rfs) > 0:
                    rnode =  self.dpc.getdxfnode( ns='refseq', ac=rfs )
                    if rnode is not None:
                        print(" Refseq match: " + rnode['ac'])
                        if ndipID != rnode['ac']:
                            print( " Node ID not unique (legacy): " + ndipID  
                                       + " (database):" + rnode['ac'])
                            node['ac'] = rnode['ac']
                            
                if gid is not None and len(gid) > 0:                        
                    gnode = self.dpc.getdxfnode( ns='entrezgene', ac=gid)
                    if gnode is not None:
                        print(" GeneId match: " + gnode['ac'])
                        if ndipID != gnode['ac']:
                            print( " Node ID not unique (legacy): " + ndipID  
                                       + " (database):" + gnode['ac'])
                            sys.exit(1, "legacy node conflict")
                
                res = self.dpc.addnode( node, mode='node' )       
                print(res.text)
                dxp = DXF.DXF15Parser()
                dxp.parse(res.text)
                
                # node dataset
                ndts = self.dpc.dom2dts(dxp.dom)                
                return ndts.node[0]
            
        else:
            # unknown
            print("Uknown node:")

            onode = None                        
            (upt,rfs,gid) = self.getNodeIdent( node.xrefList.xref)
            print((upt,rfs,gid))
                
            # find by uniprot
            if upt is not None:                
                res =  self.dpc.getnode( ns='uniprotkb', ac=upt )
                
                dxp = DXF.DXF15Parser()
                dxp.parse(res.text)
                # node dataset
                odts = self.dpc.dom2dts(dxp.dom)
 
                if odts is not None:
                    print(" By uniprot match:" + odts['node'][0]['ac'] )
                    onode = odts

            # find by refseq
            if onode is None and rfs is not None:

                res =  self.dpc.getnode( ns='refseq', ac=rfs )
                #print(res.text)

                dxp = DXF.DXF15Parser()
                dxp.parse(res.text)
                # node dataset
                odts = self.dpc.dom2dts(dxp.dom)
                if odts is not None:
                    print(" By refseq match:" + odts['node'][0]['ac'] )
                    onode = odts                        
                    
            # find  by geneid
            if onode is None and gid is not None:
                res =  self.dpc.getnode( ns='entrezgene', ac=gid )
                print(res.text)

                dxp = DXF.DXF15Parser()
                dxp.parse(res.text)
                # node dataset
                odts = self.dpc.dom2dts(dxp.dom)
                if odts is not None:
                    print(" By geneid match:" + odts['node'][0]['ac'] )
                    onode = odts

            if onode is not None:
                print(" Old node match")
                i['node'] = onode  # substitute by db record
            else:
                print("New node: uploading")
                res =  self.dpc.addnode( inode, mode='node' )
                    
                dxp = DXF.DXF15Parser()
                dxp.parse(res.text)
                
                # node dataset
                ndts = self.dpc.dom2dts(dxp.dom)                
                
                return ndts
        
        return None

    def getNodeIdent(self, xlist, sanitize = True ):

        upt = None
        rfs = None
        gid = None
        for x in xlist:
            print(x)
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

    
