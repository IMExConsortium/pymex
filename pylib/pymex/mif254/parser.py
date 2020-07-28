# -*- coding: utf-8 -*-
"""
Created on Mon Jun 29 13:56:57 2020
@author: andrei
"""
#-------------------- IMPORTS -----------------------------------------------------------------------

# -*- coding: utf-8 -*-
from lxml import etree
import json

from mif254.utils import *

def genericSearch( entry, item ):
    """Recursive search through element tree."""
    
    tag = modifyTag(item)
    
    if item.text and len(item)==0: # We have reached a leaf node: does it have attributes or not?      
        if not item.attrib:
            return item.text  
        else:
            return {"text": item.text,"elementAttrib": attribToDict( item.attrib )  }
     
    elif tag == "names":
        names = Names( entry )
        return names.parseDom( item )
        #print(tag,'c')
    elif tag == "xref":
        xref = Xref( entry )
        return xref.parseDom( item )
        #print(tag,'d')
    elif tag == "attributeList":
        #attributeList = AttributeList( entry )
        return Attribute(entry).parseDom( item )
    
    elif tag in LISTED_ELEMENTS:
        return ListedElement(entry).parseDom(item)
    
    elif isCvTerm(item):
        cvterm = CvTerm(entry)
        return cvterm.parseDom( item )
    
    else:
        data={}
        if item.attrib:
            data["elementAttrib"]=attribToDict(item.attrib)

        for child in item: 
            tag = modifyTag(child)
            data[tag] = genericSearch( entry, child )

        #print(tag,'f')
    
        return data

#------------------------------ CLASSES ------------------------------------------------------

class Mif254Parser():
    """Parses a mif file associated with a filename. Saves to Mif254Record object."""

    def __init__(self,debug=False):
        self.debug = debug
        
    def parse( self, filename ):    
        mif = Mif254Record()
        mif.parseDom( filename )
        return mif

class Mif254Record():
    """Mif record representation."""

    def __init__(self):
        self.root = []
        
    def parseDom( self, filename ):
        
        record = etree.parse( filename )
        entries = record.xpath( "/x:entrySet/x:entry", namespaces=NAMESPACES )
        for entry in entries:
            entryElem = Entry( self.root )
            self.root.append( entryElem.parseDom( entry ) )

    def fromJson(self, file ):
        self.root = json.load( file )
        return self

    def toJson(self):
        return json.dumps(self.root, indent=2)

    def toMif254( self ):
       
        rootDom = etree.Element(MIF + "entrySet", nsmap=NSMAP)
        # required attributes:
        # level="2" version="5" minorVersion="4"
 
        rootDom.set("level","2")
        rootDom.set("version","5")
        rootDom.set("minorVersion","4")
    
        for entry in self.root:
            entryDom = etree.SubElement( rootDom, MIF + "entry" )            
            Entry( self.root ).toMif254( entryDom, entry, 1 ) 
            
        return etree.tostring( rootDom, pretty_print=True )
    
class Entry():
    
    def __init__( self, root ):
        self.data = {}
        self.root = root
        
        
    def toMif254( self, parent, entry, curid ):
        if "source" in entry:
            sourceDom = etree.SubElement( parent, MIF + "source" )
            curid = Source( self.root ).toMif254( sourceDom, entry["source"], curid )
            
        # interaction list only (this enforces expanded version) 
        if "interaction" in entry and len(entry["interaction"]) > 0:
            intnListDom = etree.SubElement( parent, MIF + "interactionList" )

            for intn in entry["interaction"]:
                intnDom = etree.SubElement( intnListDom, MIF + "interaction" )
                
                intnDom.set("id", str(curid))
                curid += 1
                curid = Interaction( self.root ).toMif254( sourceDom, intn,curid )
                            
    def parseDom( self, dom ):

        for item in dom:
            tag = item.tag[LEN_NAMESPACE:]            
            if tag == 'source':
                self.data["source"] = Source( self.data ).parseDom( item )
                
            elif tag == 'experimentList':
                self.data["experiment"] = {}
                expElem = item.xpath( "x:experimentDescription", namespaces=NAMESPACES )            
                for exp in expElem:                    
                    (cId, cExp) =  Experiment( self.data ).parseDom( exp )                    
                    self.data["experiment"][cId] = cExp
                
            elif tag == 'interactorList':
                self.data["interactor"] = {}
                intrElem = item.xpath( "x:interactor", namespaces=NAMESPACES )
                for intr in intrElem:
                    (cId, cInt) =  Interactor( self.data ).parseDom( intr )
                    self.data["interactor"][cId] = cInt 

            elif tag == 'interactionList':
               self.data["interaction"] = []
               intnElem = item.xpath( "x:interaction", namespaces=NAMESPACES )
               for intn in intnElem:
                   (cId, cIntn) =  Interaction( self.data ).parseDom( intn )
                   self.data["interaction"].append( cIntn )
            elif tag == 'availabilityList':
                self.data["availability"] = {}
                avlbElem = item.xpath( "x:availability", namespaces=NAMESPACES )
                for avlb in avlbElem:
                    (cId, cAvlb) =  Availability( self.data ).parseDom(  avlb  )
                    self.data["availability"][cId] = cAvlb
        
        return self.data

class Source():
    
    def __init__( self, entry ):
        self.data={}
        self.entry = entry

    def toMif254( self, parent, source, curid ):
        # build source content here
        return curid
        
    def parseDom( self, dom ):
        if(isinstance( dom, str)):
            record = etree.parseDom( dom )
            dom = record.xpath( "/x:entrySet/x:entry/x:source",
                                namespaces=NAMESPACES )[0]        
       
        for item in dom:
            tag = modifyTag(item)
            self.data[tag] = genericSearch( self.entry, item )
            
        #element without id attribute: return data
        return self.data
 
class Experiment():
    def __init__( self, entry ):
        self.data = {}
        self.entry = entry
        
    def parseDom( self, dom ):

        if(isinstance(dom, str)):
            record = etree.parseDom( dom )
            dom = record.xpath( "/x:entrySet/x:entry/x:experimentList/x:experiment",
                                namespaces=NAMESPACES)[0]
        
        id = dom.xpath("./@id", namespaces=NAMESPACES )
        
        for item in dom:
            tag = modifyTag(item)
            self.data[tag] = genericSearch( self.entry, item )

        #element with id attribute: return (id,data) tuple   
        return ( id[0], self.data )
        
class Interactor():
    def __init__( self, entry ):
        self.data={}
        self.entry = entry

    def parseDom( self, dom ):

        if(isinstance(dom, str)):
            record = etree.parseDom(dom)
            dom = record.xpath( "/x:entrySet/x:entry/x:interactorList",
                                namespaces=NAMESPACES)[0]
            
        id = dom.xpath("./@id", namespaces=NAMESPACES )

        for item in dom:
            tag = modifyTag(item)
            self.data[tag] = genericSearch( self.entry, item )

        #element with id attribute: return (id,data) tuple   
        return ( id[0], self.data )

class Interaction():
    def __init__( self, entry ):
        self.data={}
        self.entry = entry



    def toMif254( self, parent, source, curid ):
        # build interaction content here
        return curid

        
    def parseDom( self, dom ):
        
        if(isinstance(dom, str)):
            record = etree.parseDom(dom)
            dom = record.xpath( "/x:entrySet/x:entry/x:interactionList",
                                namespaces=NAMESPACES)[0]       
        
        idata = {}
        id = dom.xpath("./@id", namespaces=NAMESPACES )
        for item in dom:
            tag = item.tag[LEN_NAMESPACE:]

            if tag == "experimentList":

                idata["experiment"] = []

                # expanded form: <experimentDescription>...</experimentDescription>
                
                expElem = item.xpath( "x:experimentDescription", namespaces=NAMESPACES )
                for exp in expElem:
                    
                    (cId, cExp) =  Experiment( self.entry ).parseDom( exp )
                    idata["experiment"].append( cExp )

                #  compact form: <experimentRef>...</experimentRef>
                    
                refElem = item.xpath( "x:experimentRef/text()", namespaces=NAMESPACES )

                for ref in refElem:       

                    idata["experiment"].append( self.entry["experiment"][ref] ) 

            elif tag == "participantList":
                idata["participant"] = []
                prtElem = item.xpath( "x:participant", namespaces=NAMESPACES )
                for prt in prtElem: 
                    (cId, cPrt) =  Participant( self.entry ).parseDom( prt )
                    idata["participant"].append( cPrt )
                
            elif tag in ["modelled","intraMolecular","negative"]:
                idata[tag] = "bool"
                
            elif tag =="confidenceList":
                idata["confidence"] = "conf"  #skip fo rnow
                
            elif tag =="parameterList":
                idata["parameter"] = "param"  #skip for now
            
            else:
                tag = modifyTag(item)
                idata[tag] = genericSearch(self.entry, item)
        # idata should look like
        #{
        # "xref": {whatever Xref.parseDom() returns}
        # "names":{whatever Names.parseDom() returns}
        # "availability": {whatever Availability.parseDom() returns
        #                  or the value corresponding to availabilityRef
        #                  taken from entry["availability"] 
        #                 },
        # "experiment": [{..},{..},{..}], the values correspond to the data        
        #                                 field returned by 
        #                                 Experiment().parseDom() or to 
        #                                 entry["experiment"] value 
        #                                 corresponding to experimentRef
        # "participant":[{..},{..},{..}], the values correspond to the data
        # ...                             field returned by 
        #}                                Participant().parseDom() 
                
        #element with id attribute: return (id,data) tuple                    
        return ( id[0], idata )

    
class Participant():
    def __init__(self, entry):
        self.data = {}
        self.entry = entry
        
    def parseDom( self, dom ):
        # parseDom participant here 
        pdata = {}
        id = dom.xpath("./@id", namespaces=NAMESPACES )
        for item in dom:
            tag = item.tag[LEN_NAMESPACE:]
            
            if tag == "interactorRef":
                pdata["interactor"] = []
                refElem= item.xpath("text()")
                for ref in refElem:

                    pdata["interactor"].append(self.entry["interactor"][ref])
            else:
                tag = modifyTag(item)
                pdata[tag] = genericSearch(self.entry,item)
        # data should look like
        #{
        # "names":{whatever Names.parseDom() returns}
        # "xref": {whatever Xref.parseDom() returns}
        # "interactor":{..}, the value corresponds        
        #                    to the data field returned by 
        #                    Interactor().parseDom() or to 
        #                    entry["interactor"] value 
        #                    corresponding
        #  "interactionRef":{ interactionRef text },
        #  "participantIdentMethod": [{..}],
        #  "biologicalRole": {},
        #  "experimentalRole":[{..}],    cvTerm (ignore expRefList for now)
        #  "experimentalPreparation":[{..}], cvTerm (ignore expRefList for now)
        #  "experimentalInteractor":[{..}], interactor (ignore expRefList for now)
        #  "feature" : [{..}],     ignore for now
        #  "hostOrganism": [{..}], ignore for now 
        #  "confidence": [{..}],   ignore for now 
        #  "parameter": [{..}],    ignore for now
        #  "attribute": [{..},{..}], the values correspond
        #                            to the values returned
        #                            by Attribute().parseDom()
        #element with id attribute: return (id,data) tuple    
        return (id[0], pdata )
    
class Names():
    def __init__(self, entry ):
        self.entry = entry
        
    def parseDom( self, dom ):        
        ndata = {}
        for item in dom:
            tag = item.tag[LEN_NAMESPACE:]
            if tag == "shortLabel" or tag == "fullName":
                ndata[tag] = item.text
            else:
                if not "alias" in ndata.keys():
                    ndata["alias"] = []
                modifiedAttrib = attribToDict(item.attrib)
                modifiedAttrib["value"] = item.text
                ndata["alias"].append(modifiedAttrib)
        # should return, eg 
        #{
        #  "shortLabel": "DIP",
        #  "fullName": "Database of Interacting Proteins",
        #  "alias: ["alias1","alias2","alias3"]
        #}        
        return ndata   
    
class Xref():
    def __init__( self, entry ):
        #self.data={}
        self.entry = entry
        
    def parseDom( self, dom ):
        #dom = dom.xpath(".",namespaces=NAMESPACES)[0]
        #self.data = genericSearch( self.entry, dom)
        xdata = {}
        id = ""
        for item in dom:
            tag = item.tag[LEN_NAMESPACE:]
            if tag == "primaryRef":
                id = item.attrib.get("db")+":"+item.attrib.get("id")
                xdata["primaryRef"] = attribToDict(item.attrib) 
                
            elif tag == "secondaryRef":
                db_id = item.attrib.get("db")+":"+item.attrib.get("id")
                attribDict = attribToDict(item.attrib)
                if not "secondaryRef" in xdata.keys():
                    xdata["secondaryRef"] = []
                    xdata["secRefInd"] = {}
                    
                xdata["secondaryRef"].append(attribDict)
                xdata["secRefInd"][db_id] = attribDict
                
        return (id, xdata)
                    
        # should return (id, data) tuple, where id is
        # set to  "db-id" + ":" + "MI:0465" (concatenation
        # db and id fields of primaryRef and
        # data is:
        #{
        # "primaryRef": {        
        #    "db": "psi-mi",
        #    "dbAc": "MI:0488",
        #    "id": "MI:0465",
        #    "refType": "identity",
        #    "refTypeAc": "MI:0356"
        #  },
        #  "secondaryRef:[
        #    {
        #     "db": "intact",
        #     "dbAc": "MI:0469",
        #     "id": "EBI-1579232",
        #     "refType": "identity",
        #     "refTypeAc": "MI:0356"
        #    },
        #    {
        #     "db": "pubmed",
        #     "dbAc": "MI:0446",
        #     "id": "14681454",
        #     "refType": "primary-reference",
        #     "refTypeAc": "MI:0358"
        #    } ]
        #}
  
class Attribute():
    def __init__( self, entry ):
        #self.data = []
        self.entry = entry
        
    def parseDom( self, dom ):
        attribdata = []
        attrDom = dom.xpath("x:attribute",namespaces=NAMESPACES)
        for attr in attrDom: 
            modifiedAttrib = attribToDict(attr.attrib)
            modifiedAttrib["value"] = attr.text
            attribdata.append(modifiedAttrib)    

        # should return 
        #{"value":"dip@mbi.ucla.edu",    
        # "name":"contact-email"
        # "nameAc":"MI:0634"
        #}
            
        return attribdata
        
class Availability():
    def __init__( self, entry ):
        self.entry = entry
        
    def parseDom( self, dom ):
        
        id = dom.attrib.get("id")
        availdata = {"value":dom.text}
        
        #element with id attribute: return (id,data) tuple
        # where data is:
        #{
        #  "value":"availability text here"
        #}
        
        return (id, availdata)
        
class CvTerm():
    def __init__(self, entry):
        self.entry = entry
        
    def parseDom( self, dom ):
        cvdata = {}
        for item in dom:
            tag = item.tag[LEN_NAMESPACE:]
            if tag == "names":                          
                cvdata["names"] = Names(self.entry).parseDom( item )    

            elif tag == "xref":                           
                cvdata["xref"] = Xref(self.entry).parseDom( item )
                
        # should return 
        #{
        #  "names": { whatever Names.parseDom() returns } 
        #  "xref": { whatever Xref.parseDom() returns}
        #}
                
        return cvdata

class ListedElement():
    def __init__(self,entry):
        self.entry = entry
    
    def parseDom( self, dom ):
        eldata = []
        for item in dom:
            eldata.append(genericSearch(self.entry,item))
            
        return eldata
