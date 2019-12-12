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

#import psimi
from lxml import etree as ET

class NodeSubmitter():
    def __init__( self, user='guest', password='guest',
                  mode='dev', debug=False ):

        self.dxfns = { 'dxf': 'http://dip.doe-mbi.ucla.edu/services/dxf15' }
        self.dpc = DP.Client()
        
    def addNode(self, doc):
                
        if isinstance( doc, ET._ElementTree) or isinstance( doc, ET._Element):            
            return self.addDxfNode(doc)
        
        if isinstance( doc, psimi.Interactor):
            return [self.addPsimiNode( doc )]

        stype = str( type(doc) )
        
        #if isinstance( doc, 'zeep.objects.nodeType'):
        if stype == "<class 'zeep.objects.nodeType'>":
            print( "#nodesubmitter: addNode(zdxf): retire me!!!!")
            #dts = self.dxf.datasetType( [node])
            return [self.addZeepNode( doc )]

        #if isinstance( doc, 'zeep.objects.datasetType'):
        if stype == "<class 'zeep.objects.datasetType'>":
            print( "#nodesubmitter: addNode(zdxf): retire me!!!!")
            ret = []
            for n in node['node']:                
                ret.append(self.addZeepNode(n))
            return ret
            
    def addPsimiNode(self, doc):
        print( "#add psimi.Interactor node: " +
               "not implemented (submit as MIF representation)" )
        # convert mif -> dxf -> zeep
        # call addDxfNode
        return None
    
    def addDxfNode(self, doc ):
        dxfNode = self.dpc.dom2dts( doc )
        stype = str(type(dxfNode))
        
        if stype == "<class 'zeep.objects.nodeType'>":
            return [self.addZeepNode( dxfNode )]
        
        if stype == "<class 'zeep.objects.datasetType'>":           
            ret = []
            for node in dxfNode['node']:
                ret.append(self.addZeepNode( node ))
            return ret
        
    def addZeepNode(self, node ):        
        if node.type.name not in ['protein','peptide']:
            print( "#ERROR: Not protein/peptide node." ) 
            return None

        ndipID = None        
        if len(node.ns) > 0 and len(node.ac) > 0:
            ndipID  = node.ac
            print("#Node ID: " + node.ns + ":" + node.ac)
        else:
            for x in node.xrefList.xref:                
                if x.type == 'identical-to' and x.ns == 'dip':
                    ndipID = x.ac
            if ndipID is not None:
                print("#Node DIP ID (by xref): " + ndipID)
            else:
                print("#Node DIP ID: N/A")
                
        if ndipID is not None:            
            # known: get node from dip
            odoc =  self.dpc.getnode( ns='dip', ac=ndipID )
            #print(odoc)
            dxp = DXF.DXF15Parser()
            dxp.parse(odoc)   # returns dom
                
            # node dataset
            ndts = self.dpc.dom2dts(dxp.dom)                
            if ndts is not None and len(ndts.node) > 0:               
                # known node
                print("#Known node:" + ndts.node[0].ac)                            
                return DXF.DXF15Record(dxp.dxf) # return (one node) record 
            else:
                # legacy/unknown node: add
                print("#Legacy(unknown) node: " + ndipID)
                print("#Legacy(unknown) node: " + node.label)
                
                (upt,rfs,gid) = self.getNodeIdent(node.xrefList.xref)
                print("# Testing ID (up/rs/gi): " + str((upt,rfs,gid)))
                # look for uniprot/refseq/genid
                    
                if upt is not None and len(upt) > 0:                    
                    unode = self.dpc.getdxfnode( ns='uniprotkb', ac=upt )
                    if unode is not None:
                        print("# Uniprot match: " + unode['ac'])
                        if  ndipID != unode['ac']:
                            print( "# Legacy node conflict")
                            print( "# Node ID not unique (legacy): " + ndipID  
                                   + " (database):" + unode['ac'])
                            
                            nm = re.search( "[0-9]+", ndipID ).group(0)
                            om = re.search("[0-9]+", unode['ac']).group(0)
                            
                            if( int(nm) < int(om) ):
                                print( "#  Updating node to legacy ID: "
                                       + unode['ac'] + " -> " + ndipID)

                                #unode['ac'] = ndipID

                                # add identical-to xref to *old* unode
                                #-------------------------------------
                                self.dpc.addxref( unode, "dip", ndipID,
                                                  type="identical-to", 
                                                  typeNs="dxf",
                                                  typeAc="dxf:0009")

                                # update node accession
                                
                                res = self.dpc.addnode( unode, mode='node-acu' )
                                dxp = DXF.DXF15Parser()
                                dxp.parse( res )                                 
                                #print( "RESULTING ID: " + str(dxp.dxf[0]['ac'] ))
                                if( dxp.dxf is not None
                                    and dxp.dxf[0]['ac'] == ndipID ):
                                    node['ac'] = ndipID

                                else:
                                    sys.exit(1, "#legacy node conflict")
                        else:     
                            node['ac'] = unode['ac']
                                
                if rfs is not None and len(rfs) > 0:
                    rnode =  self.dpc.getdxfnode( ns='refseq', ac=rfs )
                    if rnode is not None:
                        print("# Refseq match: " + rnode['ac'])
                        if ndipID != rnode['ac']:
                            print( "# Node ID not unique (legacy): " + ndipID  
                                       + " (database):" + rnode['ac'])
                            sys.exit(1, "#legacy node conflict")
                        node['ac'] = rnode['ac']
                            
                if gid is not None and len(gid) > 0:                        
                    gnode = self.dpc.getdxfnode( ns='entrezgene', ac=gid)
                    if gnode is not None:
                        print("# GeneId match: " + gnode['ac'])
                        if ndipID != gnode['ac']:
                            print( "# Node ID not unique (legacy): " + ndipID  
                                       + " (database):" + gnode['ac'])
                            sys.exit(1, "#legacy node conflict")
                        node['ac'] = gnode['ac']
                        
                res = self.dpc.addnode( node, mode='node' )
                dxp = DXF.DXF15Parser()
                dxp.parse( res )   # returns dom
                
                # node dataset
                ndts = self.dpc.dom2dts(dxp.dom)                
                if ndts is not None and len(ndts.node) > 0:               
                    # known node
                    print("#Legacy node added:" + ndts.node[0].ac)                            
                return DXF.DXF15Record(dxp.dxf) # return (one node) record 
 
        else:
            # unknown
            print("#Unknown node:")
            #print(node)
            onode = None
            #and node['attrList'] is not None
            (upt,rfs,gid) = self.getNodeIdent( node.xrefList.xref)
            if 'attrList' in node and node['attrList'] is not None and 'attr' in node['attrList']:
                (seq) = self.getNodeSequence( node.attrList.attr)
            else:
                seq = None
            (taxid, taxname) = self.getNodeTaxon( node.xrefList.xref )
            print("# Unknown node: " + node.label)
            print("# Testing ID (up/rs/gi): " + str((upt,rfs,gid)) )

            if seq is not None:                
                if len(seq) > 64:
                    print( "# Testing ID (seq:" + str(len(seq))+"): " +
                           str(seq[0:64] + "...") )
                else:
                    print( "# Testing ID (seq):" + str(len(seq))+"): " +
                           str(seq[0:64]) )
            else:
                print("# Testing ID (seq): N/A" )
                
            # find by uniprot
            if upt is not None:                
                res =  self.dpc.getnode( ns='uniprotkb', ac=upt )            
                dxp = DXF.DXF15Parser()
                dxp.parse( res )
                # node dataset
                odts = self.dpc.dom2dts(dxp.dom)            
                if odts is not None:
                    if odts['node'] is not None and len(odts['node']) > 0:
                        if len(odts['node']) == 1:
                            print( "# By uniprot match:" +
                                   odts['node'][0]['ac'] )
                            onode = res
                        else:
                            print( "# Dupliceted uniprot match:" +
                                   odts['node'][0]['ac'] )
                            sys.exit(1, "#uniprot accession conflict")
                            
            # find by refseq
            if onode is None and rfs is not None:
                res =  self.dpc.getnode( ns='refseq', ac=rfs )
                dxp = DXF.DXF15Parser()
                dxp.parse(res)
                # node dataset
                odts = self.dpc.dom2dts(dxp.dom)
                if odts is not None:
                    if odts['node'] is not None and len(odts['node']) > 0:
                        if len(odts['node']) == 1:
                            print( "# By refseq match:" +
                                   odts['node'][0]['ac'] )
                            onode = res
                        else:
                            print( "# Dupliceted refseq match:" +
                                   odts['node'][0]['ac'] )
                            sys.exit(1, "#refseq accession conflict")
                                                
            # find  by geneid
            if onode is None and gid is not None:
                res =  self.dpc.getnode( ns='entrezgene', ac=gid )
                dxp = DXF.DXF15Parser()
                dxp.parse(res)
                # node dataset
                odts = self.dpc.dom2dts(dxp.dom)
                if odts is not None:
                    if odts['node'] is not None and len(odts['node']) > 0:
                        if len(odts['node']) == 1:
                            print( "# By geneid match:" +
                                   odts['node'][0]['ac'] )
                            onode = res
                        else:
                            print( "# Dupliceted geneid match:" +
                                   odts['node'][0]['ac'] )
                            sys.exit(1, "#geneid accession conflict")

            # find  by sequence/species 
            if onode is None and seq is not None:                
                res = self.dpc.getnode( sequence=seq )
                dxp = DXF.DXF15Parser()
                dxp.parse( res )
                
                for n in dxp.dxf:                
                    for x in n['xref']:
                        if x['ns'].lower() == 'taxid':
                            print("# Taxid: " +  x['ac'] )
                            
                            if x['ac'] == taxid:
                                dxfrec = DXF.DXF15Record( n )
                                print( "# By sequence/taxid match: "
                                       + dxfrec.node[0].ac)
                                print("# Old node match.\n")
                                return dxfrec  # return (one node) record                            
                                #break

            if onode is not None:   # dxf string here...
                print("# Old node match.\n")
                dxp = DP.DXF15Parser()
                dxp.parse( onode )
                    
                return DXF.DXF15Record( dxp.dxf ) # return (one node) record
            
            else:

                if upt is None and rfs is None and gid is None and seq is None:
                    print("#Zombie node: skipping")
                    
                else:
                    print("#New node: uploading")
                    res =  self.dpc.addnode( node, mode='node' )
                
                    dxp = DXF.DXF15Parser()
                    dxp.parse( res  )   # returns dom
                
                    # node dataset
                    ndts = self.dpc.dom2dts(dxp.dom)                
                    if ndts is not None and len(ndts.node) > 0:               
                        # known node
                        print("#New node added:" + ndts.node[0].ac)                            
                        return DP.DXF15Record( dxp.dxf ) # return (one node) record 
                
        return None

    def getNodeIdent(self, xlist, sanitize = True ):

        upt = None
        rfs = None
        gid = None
        for x in xlist:        
            if x['type'] == 'identical-to':
                if x['ns'] == "uniprotkb":
                    upt = x['ac']

                    if sanitize:                        
                        # sanitize uniprot (drop version/isoform)
                        upt = re.sub( '(-[0-9]+)?((\.[0-9]+)|(\.[A-Za-z]+_\d+))?',
                                      '', upt)                     
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

    def getNodeTaxon(self, xlist ):

        taxid = None
        taxname = None
    
        for x in xlist:        
            if x['type'] == 'produced-by':
                taxid = x['ac']
                try:
                    taxname=x['node']['name']
                except:
                    print("taxname: missing")
    
        return (taxid,taxname)

    def getNodeSequence(self, alist, sanitize = True ):

        seq = None
        for a in alist:
            if a['name'] == 'sequence':
                if 'value' in a:
                    seq = a['value']['_value_1']                    
                    if sanitize:                        
                        # sanitize uniprot (drop version/isoform)
                        seq = re.sub('[^A-Za-z]+','', seq ).upper()                     
                        a['value']['_value_1'] = seq

        if seq is not None and len(seq) == 0:
            seq = None
                        
        return (seq)
    
