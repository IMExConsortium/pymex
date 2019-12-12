import sys

from http.client import HTTPSConnection, HTTPResponse
import json
import re
import ssl
import dxf as DXP
import dippy as DP
import time

from requests import Session
from requests.auth import HTTPBasicAuth

#import pymex.psimi

import zeep
from zeep import Client as zClient, Settings as zSettings
from zeep.transports import Transport

from lxml import etree as ET

class Client():
    """DIP database SOAP client. Functions should return only text/serialized 
    dxf15 records."""

    def __init__( self, user='guest', password='guest',
                  mode='dev', debug=False ):

        self.dxfns = { 'dxf': 'http://dip.doe-mbi.ucla.edu/services/dxf15' }

        self.user = user
        self.password = password
        self.mode = mode
        self.debug = debug
                
        url = 'http://10.1.200.100:8080/service/soap?wsdl'
 
        if mode == 'dev':
            url = 'http://10.1.200.100:8080/service/soap?wsdl'
            
        if self.debug:
            print(url)
            print(self.user)
            print(self.password)

        self._zsettings = zSettings( strict=False, xml_huge_tree=True,
                                     raw_response=True )
        
        self._zsession = Session()
        self._zsession.varify = False
        # self._zsession.auth = HTTPBasicAuth(self.user, self.password) 

        self._zclient = zClient(url,
                                settings=self._zsettings,                                
                                transport=Transport(session=self._zsession))
        
        self._dxfactory = self._zclient.type_factory('ns1')
        self._ssfactory = self._zclient.type_factory('ns0')
        
        if self.debug:
            print(self.zclient)
            print("\nDONE: __init__") 

    @property
    def zdxf(self): 
        return self._dxfactory

    @property
    def ssf(self):
        return self._ssfactory

    
    def getstatus( self, detail='default', format='dxf15' ):
        # -> node: ns1:nodeType[]
        
        try:
            status = self._zclient.service.status( detail, format )
    
            return status
        
        except Exception as e:
             print( type(e) )

        return None
                   
    def getentry( self, pmid ):

        ident = self._zfactory.identifier(ns= 'pmid',ac= pmid.rstrip())

        try:                                    
            r_fnd = self.zclient.service.getPublicationById( identifier=ident )
            return r_fnd
                    
        except Exception as e:
            print( type(e) )
            print( "PMID:"+ str(pmid) + " :: No record found" )
            
        return None

    def getevid(self, ns='', ac='', match='evidence', detail='',format=''):

        try:                                    
            nodes_found = self._zclient.service.getEvidence( ns = ns,
                                                             ac = ac,
                                                             match = match,
                                                             detail = detail,
                                                             format = format)            
            return nodes_found
        
        except Exception as e:
            print( type(e) )
            print( "ns/ac/match:" + str(ns) +
                   "/" + str(ac) + "/" + str(match) + " :: No records found" )
            
        return None
    
    def getnode(self, ns='', ac='', sequence='', match='', detail='',format=''):

        try:
            print("****" + ns + "::::" + ac )
            n_fnd = self._zclient.service.getNode( ns = ns,
                                                   ac = ac,
                                                   sequence = sequence,
                                                   match = match,
                                                   detail = detail,
                                                   format = format)

            if n_fnd.status_code == 200:
                print(n_fnd.text)
                return n_fnd.text
            else:
                sys.exit(1)
                
        except Exception as e:
            print( type(e) )
            print( "ns/ac/match:" + str(ns) +
                   "/" + str(ac) + "/" + str(match) + " :: No records found" )
            
        return None


    def getdxfnode( self, ns='', ac='', sequence='', match='',
                    detail='', format=''):

        print("#dippyclient: getdxfnode: depreciated !!!")
        
        res = self.getnode( ns=ns, ac=ac, sequence=sequence,
                            match=match, detail=detail,format=format )
        if res is not None:
            dxp = DXF.DXF15Parser()
            dxp.parse(res)
                
            # node dataset
            dts = self.dom2dts(dxp.dom)
            if dts is not None and len(dts['node']) > 0:
                return dts['node'][0]
        
        return None
    
    def addnode( self, node, mode='node' ):

        stype = str(type(node))
        print("#DIPPYClient-> addnode: " + stype)
                
        #if isinstance( node, 'zeep.objects.nodeType'):        
        if stype == "<class 'zeep.objects.nodeType'>":
            print("#dippyclient: addnode(zdxf): retire me!!!!")
            dts = self.zdxf.datasetType( [node])
            dts['level']= "1"
            dts['version']= "5"

        #if isinstance( node, 'zeep.objects.datasetType'):    
        if stype == "<class 'zeep.objects.datasetType'>":
            print("#dippyclient: addnode(zdxf): retire me!!!!")
            dts = node
            
        if isinstance( node, ET._ElementTree):
            #print(ET.tostring(node))
            dts = self.dom2dts( node )
            #print(dts)
        try:
            #print(dts)
            nnodes = self._zclient.service.setNode( dts, mode)
            return nnodes.text
        except Exception as e:
            print( "dippyclient: addnode" )
            print( type(e) )
             
        return None

    def getexpt(self, ns='', ac='', match='', detail='',format=''):
        print("#getexpt ns/ac/match: " + ns + ":" + ac + ":" + match)
        try:                                    
            expts_found = self._zclient.service.getEvidence( ns = ns,
                                                             ac = ac,
                                                             match = match,
                                                             detail = detail,
                                                             format = format)            
            return expts_found

        except Exception as e:
            print( type(e) )
            print( "ns/ac/match:" + str(ns) +
                   "/" + str(ac) + "/" + str(match) + " :: No records found" )
            
        return None

    
    def addexpt( self, doc ):
        print("#DIPPYClient-> addexpt:")
        stype = str(type(doc))
        print("#"+stype)
        #if isinstance(doc, 'zeep.objects.nodeType'):        
        if stype == "<class 'zeep.objects.nodeType'>":
            print("#dippyclient: addexpt(zdxf): retire me!!!!")            
            dts = self.zdxf.datasetType( [doc])

        #if isinstance( doc, 'zeep.objects.datasetType'):    
        if stype == "<class 'zeep.objects.datasetType'>":
            print("#dippyclient: addexpt(zdxf): retire me!!!!")          
            dts = doc
            
        if isinstance( doc, psimi.interaction.Interaction):
            idxf = self.interaction2dxfExpt( doc )
            dts = self.zdxf.datasetType( [idxf])

        if isinstance( doc, ET._ElementTree):        
            dts = self.dom2dts( doc )          
            
        try:            
            nexpt = self._zclient.service.setEvidence( dts, 'experiment')
            return nexpt            
        except Exception as e:           
             print( "#"+str(type(e)) )

        return None

    def addevid( self, doc ):
        print("#DIPPYClient-> addevid:")
        stype = str(type(doc))
        print("#"+stype)
        #if isinstance(doc, 'zeep.objects.nodeType'):        
        if stype == "<class 'zeep.objects.nodeType'>":
            print("#dippyclient: addevid(zdxf): retire me!!!!")            
            dts = self.zdxf.datasetType( [doc])

        #if isinstance( doc, 'zeep.objects.datasetType'):    
        if stype == "<class 'zeep.objects.datasetType'>":
            print("#dippyclient: addevid(zdxf): retire me!!!!")            
            dts = doc
            
        if isinstance( doc, psimi.interaction.Interaction):
            idxf = self.interaction2dxfExpt( doc )
            dts = self.zdxf.datasetType( [idxf])

        if isinstance( doc, ET._ElementTree):        
            dts = self.dom2dts( doc )          
            
        try:            
            nexpt = self._zclient.service.setEvidence( dts, 'evidence')
            return nexpt            
        except Exception as e:           
             print( "#"+str(type(e)))

        return None

    def addedge( self, doc, mode='edge' ):

        stype = str(type(doc))
        print("#DIPPYClient-> addedge: " + str(stype))
        
        if isinstance( doc, psimi.interaction.Interaction):
            idxf = self.interaction2dxfExpt( doc )
            dts = self.zdxf.datasetType( [idxf])

        if isinstance( doc, ET._ElementTree):        
            dts = self.dom2dts( doc )
            
            #nexp = self.ndom2dxf( doc, cid = 1 )
            #dts = self.zdxf.datasetType( [nexp])

            
        #if isinstance(doc, 'zeep.objects.nodeType'):        
        if stype == "<class 'zeep.objects.nodeType'>":
            print( "#dippyclient: addedge(zdxf): retire me!!!!" )
            dts = self.zdxf.datasetType( [doc] )
            dts['level']= "1"
            dts['version']= "5"

        try: 
            nexpt = self._zclient.service.setLink( dts, mode )
            return nexpt.text
        except Exception as e:           
             print( "#"+str(e) )

        return None


    def getsource( self, ns='', ac='', sequence='', match='',
                   detail='', format=''):

        try:                                    
            src_found = self._zclient.service.getSource( ns = ns,
                                                         ac = ac,
                                                         match = match,
                                                         detail = detail,
                                                         format = format)            
            return src_found
        
        except Exception as e:
            print( "#"+ str(type(e)) )
            print( "#ns/ac/match:" + str(ns) +
                   "/" + str(ac) + "/" + str(match) + " :: No records found" )            
        return None

        
    def addsource( self, dom, mode='source' ):

        if isinstance( dom, ET._ElementTree):
            dts = self.dom2dts( dom )
        else:
            dts = dom
        try:
            nsource = self._zclient.service.setSource( dts, mode)
            return nsource
        except Exception as e:           
             print( "#" + str(type(e)) )

        return None

    def addimex( self, ns='dip', ac='', imexid='',
                 record='', format='mif254' ):

        try:
            nsource = self._zclient.service.setImexSRec( ns = ns,
                                                         ac = ac,
                                                         imxid = imexid,
                                                         record = record,
                                                         format = format)
            return nsource
        except Exception as e:           
            print( "#" + str(type(e)) )
             
        return None

    
    def dom2dts( self, dom ):

        dxnl = []
        cid = 1

        if isinstance( dom, ET._ElementTree):
            root = dom.getroot()
        else:
            root = dom

        for ndom in root.getchildren():
            #for ndom in root.iter("{*}node"):
            #print(type(dom))
            #print(("root/node",root,ndom))
            (dxn, cid ) = self.ndom2dxf( ndom, cid )  
            dxnl.append( dxn )
            #print(dxnl)

        dts = self.zdxf.datasetType( dxnl )
        dts.level="1"
        dts.version="5"
            
        return dts

    
    def ndom2dxf( self, ndom, cid = 1 ):
        
        dxf = self.zdxf

        cid = None
        cns = None
        cac = None
        cname = None
        clabel = None
        ctype = None
        cxref = None
        cattr = None
        cpart = None

        cid = ndom.get("id")        
        cac = ndom.get("ac")        
        cns = ndom.get("ns")
              
        for cc in ndom.getchildren():
            
            # <type>      
            if cc.tag.endswith("type"):
                ctype = dxf.typeDefType( ns=cc.get("ns"),
                                         ac=cc.get("ac"),
                                         name=cc.get("name") )
            # <label>            
            if cc.tag.endswith("label"):
                clabel = cc.text

            # <name>            
            if cc.tag.endswith("name"):
                cname = cc.text

            # <xrefList>
            if cc.tag.endswith("xrefList"):
                cxref = {'xref':[]}

                for cx in cc.getchildren():
                    
                    txn = None
                    
                    if cx.getchildren():
                        (txn, cid) = self.ndom2dxf( cx.getchildren()[0] )

                    dxref = dxf.xrefType( ns = cx.get("ns"), ac = cx.get("ac"),
                                          typeNs = cx.get("typeNs"),
                                          typeAc = cx.get("typeAc"),
                                          type = cx.get("type"),
                                          node = txn )
                    cxref["xref"].append(dxref)

            # <attrList>            
            if cc.tag.endswith("attrList"):                
                cattr = {'attr':[]}

                for ca in cc.getchildren():
                    cv = ca.find("dxf:value",  namespaces = self.dxfns)                                       
                    if cv is not None:
                        cval = cv.text
                        
                        dxatt = dxf.attrType( value = cval,
                                              ns = ca.get("ns"),
                                              ac = ca.get("ac"),
                                              name = ca.get("name"))

                        if(cv.get("ns") is not None):
                            dxatt.value.ns=cv.get("ns") 

                        if(cv.get("ac") is not None):
                            dxatt.value.ac=cv.get("ac") 
                        
                        cattr["attr"].append( dxatt )

            # partList
            if cc.tag.endswith("partList"):                
                cpart = {'part':[]}
                
                for cp in cc.getchildren():
                         
                    cpid = cp.get("id")
                    cpname = cp.get("name")
                    
                    for cpe in cp.getchildren():
                        if cpe.tag.endswith("type"):
                            cptype = dxf.typeDefType( ns=cpe.get("ns"),
                                                      ac=cpe.get("ac"),
                                                      name=cpe.get("name") )
                            
                        if cpe.tag.endswith("node"):
                            (cpnode,cid) =  self.ndom2dxf( cpe, cid = 1 )

                    
                    dxpart = dxf.partType(id = cpid,
                                          name = cpname,
                                          type = cptype,
                                          node = cpnode);
                    cpart['part'].append(dxpart)        
                    
        dxn = dxf.nodeType( id = cid, ns = cns, ac = cac,
                            name = cname,
                            type = ctype,
                            label= clabel,
                            xrefList = cxref,
                            attrList = cattr,
                            partList = cpart)
                    
        return (dxn, cid)

    
    def prot2dxf( self, ir, cid = 1 ):

        ns = None
        ac = None        
        for x in ir.sxref:
            #  1st priority: DIP node 
            if x['nsAc'] == 'MI:0465':
                ns='dip'
                ac=x['ac']                    
                break

            #  2st priority: isoform parent (if present)
            if 'refType' in x:
                if x['refType'] == 'isoform-parent' and x['ns'] == 'uniprotkb':
                    ns = 'uniprotkb'
                    ac = x['ac']
                    # clean up isoform id
                    if '-' in ac:
                        ac = ac.split('-')[0]

        #  1st priority: DIP node 
        if ir.pxref['nsAc'] == 'MI:0465':
            ns='dip'
            ac=ir.pxref['ac']
                
        # 3rd priority: primary id 
        if ns == None:                
            ns = ir.pxref['ns']
            ac = ir.pxref['ac']
                    
        #print(ir.pxref)
        #print('ns: ' + ns + ' ac: ' + ac)
            
        dxf = self._dxfactory

        # label/name/accession/type
        #--------------------------
                
        protType = dxf.typeDefType( ns='dxf', ac='dxf:0003', name='protein')
        prot = dxf.nodeType(id=1, ns= ns, ac=ac,
                            label=ir.label, name=ir.name,
                            type=protType,
                            xrefList = {'xref':[]})
        # taxon
        #------
                
        txType = dxf.typeDefType( ns='dxf', ac='dxf:0301', name='organism')                                
        txNode = dxf.nodeType(id=2, ns='taxid', ac=ir.species['ac'],
                              label=ir.species['label'],
                              name=ir.species['name'],
                              type=txType)
                
        txRef = dxf.xrefType( typeNs="dxf", typeAc="dxf:0007",
                              type="produced-by",
                              node = txNode,
                              ns=ir.species['ns'],
                              ac=ir.species['ac'])
        
        prot.xrefList.xref.append(txRef)

        # xrefs
        #------               

        if ir.pxref['ac'] != ac:
            if ('refType' in ir.pxref and ir.pxref['refType'] == 'identity') or ('refTypeAc' in ir.pxref and ir.pxref['refTypeAc']  == 'MI:0356'):
            
                pxRef = dxf.xrefType( typeNs="dxf", typeAc="dxf:0009",
                                          type="identical-to",                                        
                                          ns=ir.pxref['ns'],
                                          ac=ir.pxref['ac'])
            else:
                pxRef = dxf.xrefType( typeNs="dxf", typeAc="dxf:0018",
                                      type="related-to",                                        
                                      ns=ir.pxref['ns'],
                                      ac=ir.pxref['ac'])
        else:
            pxRef = dxf.xrefType( typeNs="dxf", typeAc="dxf:0009",
                                  type="identical-to",                                        
                                  ns=ir.pxref['ns'],
                                  ac=ir.pxref['ac'])
                
        prot.xrefList.xref.append(pxRef) 
            
        for sx in ir.sxref:
            if sx['ac'] != ac:
                if ('refType' in sx and sx['refType'] == 'identity') or ('refTypeAc' in sx and sx['refTypeAc']  == 'MI:0356'):
                    sxRef = dxf.xrefType( typeNs="dxf", typeAc="dxf:0009",
                                          type="identical-to",                                        
                                          ns=sx['ns'],
                                          ac=sx['ac'])
                else:
                    sxRef = dxf.xrefType( typeNs="dxf", typeAc="dxf:0018",
                                          type="related-to",                                        
                                          ns=sx['ns'],
                                          ac=sx['ac'])

            else:                
                sxRef = dxf.xrefType( typeNs="dxf", typeAc="dxf:0009",
                                      type="identical-to",                                        
                                      ns=sx['ns'],
                                      ac=sx['ac'])
                        
            prot.xrefList.xref.append(sxRef) 
                    
        return prot

    def dom2exp( self, dom, cid = 1 ):
        dxf = self._dxfactory
                
        expType = dxf.typeDefType( ns='dxf', ac='dxf:0049', name='experiment')
        exp = dxf.nodeType(id=1, ns="dip", ac="",
                           label=dom.label,
                           type=expType,
                           xrefList = {'xref':[]},
                           attrList = {'attr':[]},
                           partList = {'part':[]})

        #print(dom.pxref)
        #print(dom.sxref)
        
        if dom.imex:

            # imex experiment (IM-12234-1) identifier
            #----------------------------------------        

            imexRef = dxf.xrefType( typeNs="dxf", typeAc="dxf:0009",
                                    type="identical-to",                                        
                                    ns='imex',
                                    ac=dom.imex)            
            exp.xrefList.xref.append(imexRef)

            exp.ns="imex"
            exp.ac= dom.imex
                        
        # dip source (DIP-1234S) identifier
        #----------------------------------
        dipSrcAc = None
        
        if dom.pxref['ns'] == 'dip':
            dipSrcAc = dom.pxref['ac']           
        else:
            for x in dom.root['source']['sxref']:
                if x['ns'] == 'dip':
                    dipSrcAc = x['ac']
                    
        if dipSrcAc is not None:
            dipRef = dxf.xrefType( typeNs="dxf", typeAc="dxf:0014",
                                   type="described-by",                                        
                                   ns='dip',
                                   ac=dipSrcAc)
            exp.xrefList.xref.append(dipRef)
            
        if len(dom.evolist) > 0:
            evo = dom.evolist[0]

            print( "#" + evo.label)
            exp.label=evo.label

            # paper pmid identifier
            #----------------------
            if evo.pmid is not None and len(evo.imex) > 0:
                imxevidRef = dxf.xrefType( typeNs="dxf", typeAc="dxf:0014",
                                           type="described-by",                                        
                                           ns='pubmed',
                                           ac=evo.pmid)
                exp.xrefList.xref.append(imxevidRef)
                
            # imex paper (IM-12345) identifier
            #---------------------------------
            if evo.imex is not None and len(evo.imex) > 0:
                imexRef = dxf.xrefType( typeNs="dxf", typeAc="dxf:0014",
                                        type="described-by",                                        
                                        ns='imex',
                                        ac=evo.imex)
                exp.xrefList.xref.append(imexRef)


            # dip experiment (DIP-1234X) identifier
            #--------------------------------------
            if evo.pxref['ns'] == 'dip' and evo.pxref['refType'] == 'identity':
                exp.ns="dip"
                exp.ac=evo.pxref['ac']
            else:
                for sx in evo.sxref:
                    print("sx" + str(sx))
                    if sx['ns'] == 'dip' and sx['refType'] == 'identity':
                        exp.ns="dip"
                        exp.ac=sx['ac']
                        print(sx)
                

            # experiment info
            #----------------

            # det method (interaction detection method)
            #------------------------------------------
            if evo.intMth is not None:
                imth = dxf.attrType( name="interaction detection method",
                                     ac="MI:0001", ns="psi-mi",
                                     value = evo.intMth['name'])
                imth.value.ns= evo.intMth['ns']
                imth.value.ac= evo.intMth['ac']                
                exp.attrList.attr.append(imth)

            # experiment host (multiple values possible)
            #----------------
                
            if evo.ehost is not None:
                for ehost in evo.ehost:
                    host = dxf.attrType( name="organism",
                                         ac="dxf:0017", ns="dxf",
                                         value = ehost['name'])
                    host.value.ns= ehost['ns']
                    host.value.ac= ehost['ac']                
                    exp.attrList.attr.append(host)


            # id method (interaction detection method)
            #--------------------------------------
            if evo.prtMth is not None and evo.prtMth['ac'] != 'MI:0661':                
                pmth = dxf.attrType( name="participant identification method",
                                     ac="MI:0002", ns="psi-mi",
                                     value = evo.prtMth['name'])
                pmth.value.ns= evo.prtMth['ns']
                pmth.value.ac= evo.prtMth['ac']                
                exp.attrList.attr.append(pmth)
                    
                
            # link type (interaction type)
            #------------------------------

            itype = dxf.attrType( name="interaction type",
                                  ac="MI:0190", ns="psi-mi",
                                  value = dom.type['name'])
            itype.value.ns= dom.type['ns']
            itype.value.ac= dom.type['ac']                
            exp.attrList.attr.append(itype)

            return exp


    def dom2int( self, dom, cid = 1 ):
        dxf = self._dxfactory
                
        lnkType = dxf.typeDefType( ns='dxf', ac='dxf:0004', name='link')
        lnk = dxf.nodeType(id=1, ns="dip", ac="",
                           label=dom.label,
                           type=lnkType,
                           xrefList = {'xref':[]},
                           attrList = {'attr':[]},
                           partList = {'part':[]})

        exp = self.dom2exp( dom )

        expRef = dxf.xrefType( typeNs="dxf", typeAc="dxf:0008",
                               type="supported-by",                                        
                               ns='',
                               ac='',
                               node = exp)            
        lnk.xrefList.xref.append( expRef )        
        return lnk

    def interaction2dxfExpt( self, dom, cid = 1 ):
        
        dxf = self._dxfactory
        exp = self.dom2exp( dom, cid )
                            
        if len(dom.ptlist) > 0:
            
            for p in dom.ptolist:
                prtType = dxf.typeDefType( ns='dxf', ac='dxf:0048',
                                           name='experiment-node')
                
                pint = self.prot2dxf( p.interactor)
                
                part = dxf.partType(id=1, 
                                    name=p.ilabel,
                                    type=prtType,
                                    node=pint,
                                    xrefList = {'xref':[]})

                if len(part.xrefList.xref) == 0:
                    part.xrefList = None
                exp.partList.part.append(part)            
        return exp
    
    def interaction2dxfIntn( self, dom, cid = 1 ):
        
        intn = self.dom2int( dom, cid )
                            
        if len(dom.ptlist) > 0:
            
            for p in dom.ptolist:
                prtType = self.zdxf.typeDefType( ns='dxf', ac='dxf:0010',
                                                 name='linked-node')
                
                pint = self.prot2dxf( p.interactor)
                
                part = self.zdxf.partType(id=1, 
                                          name=p.ilabel,
                                          type=prtType,
                                          node=pint,
                                          xrefList = {'xref':[]})

                if len( part.xrefList.xref ) == 0:
                    part.xrefList = None
                intn.partList.part.append( part )            
        return intn
    

    def addxref( self, node, ns, ac, xrefnode = None,
                 type=None, typeNs=None, typeAc=None ):

        if node is None:
            return None
        
        if type is None:
            type = "related-to"
            typeNs = "dxf"
            typeAc = "dxf:0018"

        txRef = self.zdxf.xrefType( typeNs=typeNs, typeAc=typeAc,
                                    type=type, node = xrefnode, ns=ns, ac=ac )

        node.xrefList.xref.append( txRef )
        return node
    
