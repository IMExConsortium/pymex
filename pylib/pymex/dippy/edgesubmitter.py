import sys
#sys.path.insert(0,"/cluster1/home/lukasz/git/psi-mi-tools/pylib")
#sys.path.insert(0,"/cluster1/home/lukasz/git/dip-backend/pylib")
#sys.path.insert(0,"/cluster1/home/lukasz/git/dip-proxy-tools/pylib")

import json
import re
import io

import dxf as DXF
import dippy as DP

import psimi
from lxml import etree as ET

class EdgeSubmitter():
    def __init__( self, user='guest', password='guest',
                  mode='dev', debug=False ):
        self.dxfns = { 'dxf': 'http://dip.doe-mbi.ucla.edu/services/dxf15' }
        self.dpc = DP.Client()
        self.nsub = DP.NodeSubmitter()
        self.vsub = DP.EvidSubmitter()

    def addEdge(self, edge, autoNode = True, autoEvid = False):

        print("\n#EdgeSubmitter.addEdge: " + str(type(edge)) )
        
        if isinstance( edge, ET._ElementTree) or isinstance( edge, ET._Element):
            # lxml-parsed dxf file: _ElementTree or Element
            return self.autoDxfEdge( edge,
                                     autoNode = autoNode,
                                     autoEvid = autoEvid )
        
        if isinstance( edge, psimi.Interaction ):
            # psimi.Interaction data structure
            return self.autoPsimiEdge( edge,
                                       autoNode = autoNode,
                                       autoEvid = autoEvid)

        
    def autoPsimiEdge( self, edge, autoNode = True, autoEvid = False):

        # psimi.Interaction data structure

        print( "#add psimi.Interaction node: "
               + "not implemented (submit as MIF representation)" )
        print( "#autoPsimiEdge: " + str(type(edge)) )
        dxe = self.dpc.interaction2dxfIntn(edge)
        dts = self.dpc.zdxf.datasetType()
        dts.node.append( dxe )
 
        print("#DTS: " + str(type(dts)))
        # dts: should be lxml-parsed dxf file: _ElementTree or Element
        
        return self.autoDxfEdge( dts, autoNode = autoNode, autoEvid = autoEvid )

    
    def autoDxfEdge( self, edge, autoNode = True, autoEvid = False ):
               
        print("#autoDxfEdge: "+ str(type(edge)))

        #print(type(edge))
        # lxml-parsed dxf file: _ElementTree or Element

        dxfEdge = self.dpc.dom2dts( edge )   # zeep

        print("#dxfEdge: " + str(type(dxfEdge)))
        #print(dxfEdge)
        print("#----------")
        if len(dxfEdge['node']) != 1:
            print("#ERROR: Multiple nodes passed.")
            return None
        
        edge = dxfEdge['node'][0]
        if edge['type']['ac'] != 'dxf:0004':
            print("#ERROR: Not edge/link node.") 
            return None

        xrefList = edge.xrefList.xref
        attrList = edge.attrList.attr
        partList = edge.partList.part

        if autoNode:
            for p in partList:
                print("#Part AC: " + p.node.ac)
                pp =  self.nsub.addNode(p.node)
                print("\n#DXF RECORD##: " + str(type(pp[0])))
                if pp is not None and pp[0] is not None:
                    domNode = pp[0]
                    #print( domNode.dxf )
                    dxp = DXF.DXF15Parser()
                    #print(domNode.dxfstr())
                    dxp.parse( domNode.dxfstr() ) # returns single-node dxf dom
                    dxfNode = self.dpc.dom2dts( dxp.dom )
                    p.node = dxfNode['node'][0] # first dataset node
                else:
                    print("#Missing node")
                    return None
        # create/update edge

        nlnk = self.buildLink( ns=edge.ns, ac= edge.ac, parts=partList,
                               xrefs=xrefList, attrs = attrList )

        nlnk = self.dpc.addedge( nlnk, mode='edge' )
       
        if not autoEvid:   # link only
            return nlnk

        #print("NLINK: type: " + str(type(nlnk)) )
        #print(nlnk)

        nldxp = DXF.DXF15Parser()
        nldxp.parse( nlnk )
        
        # expt dataset (from database)
        nldts = self.dpc.dom2dts( nldxp.dom )

        for x in xrefList:    
            if x.type in ['supported-by']:
                print("#Experiment ID: " + x.ns + ":" + x.ac)

                pexpt = self.dpc.getexpt( ns='dip', ac=x.ac,
                                          match='experiment' )
                pxdxp = DXF.DXF15Parser()
                pxdxp.parse( pexpt.text )

                # expt dataset (from database)
                xdts = self.dpc.dom2dts( pxdxp.dom )

                if xdts is not None:
                    print( "# Old expt: " + xdts.node[0].ac)
                    if x.node is not None:
                        print( "#   New details (ignored): " + str(x.node.ac))   

                else:
                    print( "# New/legacy expt" )

                    if x.node is None:
                        print( "# Experiment description missing!!!" )
                    else:
                        print( "# Explicit parts: " + str(x.node.partList))

                        if x.ac.endswith("X"):

                            # experiment hiding as dip evidence

                            x.node.type.ns='dxf'
                            x.node.type.ac='dxf:0063'
                            x.node.type.name='experiment'

                            org = False
                            for na in x.node.attrList.attr:                                
                                if na.name in ['organism','taxon']:
                                    org = True 

                            if not org:
                                # add not specified
                                print("#org missing -> set to unspecified")

                                orgAtt=self.dpc.dxf.attrType( ns="dxf",
                                                              ac="dxf:0017",
                                                              name="organism",
                                                              value="unspecified")
                                orgAtt.value.ns= 'taxid'
                                orgAtt.value.ac = '0'

                                x.node.attrList.attr.append(orgAtt)

                            if x.node.partList is None:
                                x.node.partList  = edge.partList

                                xsub = DP.ExptSubmitter()
                                xdts = xsub.addExpt( x.node )
                                print( "# New expt: " + xdts.node[0].ac)

                #  add evid

                if xdts is None:
                    print("#experiment missing")
                    sys.exit(1)
                else:
                    print("#trying evidence")    
                    # get direct assay evid by exp accession
                    # 
                    pexpt = self.dpc.getexpt( ns='dip', ac=x.ac , match ='evid')
                    pxdxp = DXF.DXF15Parser()
                    pxdxp.parse( pexpt.text )                    
                    # expt dataset (from database)
                    pxdts = self.dpc.dom2dts( pxdxp.dom )
                    #print(pxdts)

                    # if evid missing - create record, submit
                    if pxdts is None:
                        evnode = self.vsub.buildDirect(xdts.node[0])
                        #print(evnode)
                        pexpt = self.dpc.addevid( evnode )
                        pxdxp = DXF.DXF15Parser()
                        pxdxp.parse( pexpt.text )                    
                        # expt dataset (from database)
                        pxdts = self.dpc.dom2dts( pxdxp.dom )

                    # add evid to edge, resubmit edge

                    print("#EVID ID: " + pxdts.node[0].ac)
                    print("#LINK ID: " + nldts.node[0].ac)

                    lnRef = None
                    for px in pxdts.node[0].xrefList.xref:
                        print( "# PX:" + px.ns +":" + px.ac +":"
                               + px.type +":" + px.typeAc) 
                        # add xref to supported link
                        if px.ns == nldts.node[0].ns and px.ac == nldts.node[0].ac and px.type=="supports":
                            lnRef = px
                            print("#   PX: breake")
                            break;

                    if lnRef is None:
                        lnRef = self.dpc.dxf.xrefType( typeNs="dxf",
                                                       typeAc="dxf:0013",
                                                       type="supports",
                                                       ns = nldts.node[0].ns,
                                                       ac = nldts.node[0].ac)            

                        pxdts.node[0].xrefList.xref.append(lnRef)
                        #print(pxdts.node[0])

                        # resubmit evid
                        pexpt = self.dpc.addevid( pxdts.node[0] ) 

                        pxdxp = DXF.DXF15Parser()
                        pxdxp.parse( pexpt.text )                    
                        # expt dataset (from database)
                        pxdts = self.dpc.dom2dts( pxdxp.dom )
                        print(pexpt.text)
                    # update edge type
                    #     colocalization -> association -> physical -> direct  
                    
        return nldxp
        #return None

    
    def buildLink(self, ns='dip', ac='', parts = None,
                  nodes = None, xrefs = None, attrs = None ):

        # generic link (of unspecified type)
        # NOTE: ignores attributes (for the moment ?)
        
        #<ns2:type name="link" ac="dxf:0004" ns="dxf"/>
        #<ns2:label>DIP-2612E</ns2:label>

        
        ltype = self.dpc.zdxf.typeDefType( ns='dxf',
                                           ac='dxf:0004',
                                           name='link' )
                 
        lntAtt = self.dpc.zdxf.attrType( ns="dip", ac="dip:0001",
                                         name="link-type",
                                         value="unspecified")
        lntAtt.value.ns = ''
        lntAtt.value.ac = ''
                
        lnode = self.dpc.zdxf.nodeType( id = 1,
                                        ns= ns,
                                        ac= ac,                                        
                                        type=ltype,
                                        label = '',
                                        name = '',
                                        attrList = {'attr':[lntAtt]},
                                        partList = {'part':[]})

        if parts is not None:
            nodes = []
            for p in parts:
                nodes.append( p.node )

        id = 1
        for n in nodes:
            
            lntype = self.dpc.zdxf.typeDefType( ns='dxf',
                                            ac='dxf:0010',
                                            name='linked-node' )
            
            pexpt = self.dpc.zdxf.partType( type = lntype,
                                            #node = n,
                                            name = '',
                                            id = id )

            pexpt['node'] = n
            lnode.partList.part.append( pexpt )
            id+=1

        if xrefs is not None:
            lnode.xrefList = {'xref':[]}
            #lnode.xrefList['xref']=[]            
            for x in xrefs:
                if x is not None and x.ac is not None: 
                    xRef = self.dpc.zdxf.xrefType( typeNs=x.typeNs,
                                                   typeAc=x.typeAc,
                                                   type=x.type,
                                                   ns=x.ns,
                                                   ac=x.ac)
                    lnode.xrefList['xref'].append(xRef)
            #print(lnode.xrefList)
                                                               
        return lnode


    
