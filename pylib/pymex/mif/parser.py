# -*- coding: utf-8 -*-
"""
Created on Mon Jun 29 13:56:57 2020
@author: andrei
"""
#-------------------- IMPORTS -----------------------------------------------------------------------
 
# -*- coding: utf-8 -*-
from lxml import etree
import json
from xml.dom import minidom
import os

from mif.utils import *
import mif.globalVars as globalVars


#------------------------------GENERIC PARSER---------------------------------------------------
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
    
    elif isListedElement(item):
        if tag=="attributeList":
            return Attribute(entry).parseDom( item )
        else:
            return ListedElement(entry).parseDom(item)
    
    elif isCvTerm(item):
        cvterm = CvTerm(entry)
        return cvterm.parseDom( item )
    
    else:
        data={}
        if item.attrib:
            if(tag in ["hostOrganism","organism"]):
                data["ncbiTaxId"] = item.attrib.get("ncbiTaxId")
            else:
                data["elementAttrib"]=attribToDict(item.attrib)
            

        for child in item: 
            tag = modifyTag(child)
            data[tag] = genericSearch( entry, child )

        #print(tag,'f')
    
        return data


#------------------------------ CLASSES ------------------------------------------------------
    

class MifParser():
    """Parses a mif file associated with a filename. Saves to Mif254Record object."""

    def __init__(self,debug=False):
        self.debug = debug
        
    def parse( self, filename, ver ):       
        mif = MifRecord()
        mif.parseDom( filename, ver )
        return mif

class MifRecord():
    """Mif record representation."""

    def __init__(self):
        self.root = {"entries":[]}
    
    @property
    def entry(self):
        return self.getEntry()
    
    def getEntry(self, id = 0):
        if len(self.root) > id:
            return Entry(self.root, id)
        else:
            return None
    
    @property          
    def interaction(self):
        
        ret = []
        
        for i in Entry( self.root ).interaction:
            ret.append( self.getEntry().getInteraction(id) )
        
        #return Entry(self.root).interaction
        return ret
        
    def __getitem__(self, id):
        return self.getEntry().getInteraction(id)
    
    def parseDom( self, filename , ver):
        """Builds a MifRecord object from an MIF XML file."""
        if(ver=="mif300"):
            globalVars.NAMESPACES = {"x":"http://psi.hupo.org/mi/mif300"}
            
        elif(ver=="mif254"):
            globalVars.NAMESPACES = {"x":"http://psi.hupo.org/mi/mif"}
        
        globalVars.LEN_NAMESPACE = len(globalVars.NAMESPACES["x"])+2
        
        record = etree.parse( filename )
        entrySet = record.xpath("/x:entrySet",namespaces=globalVars.NAMESPACES)
        for key, val in entrySet[0].attrib.items():
            self.root[key] = val
        entries = record.xpath( "/x:entrySet/x:entry", namespaces=globalVars.NAMESPACES )
        for entry in entries:
            entryElem = Entry( self.root )
            self.root["entries"].append( entryElem.parseDom( entry ) )

    def parseJson(self, file ):
        self.root = json.load( file )
        return self

    def toJson(self):
        return json.dumps(self.root, indent=2)
                
    def toMif( self , ver):
        """Builds a MIF elementTree from a MifRecord object."""
        
        json_dir = os.path.dirname(os.path.realpath(__file__))
        
        if(ver=="mif300"):
            nsmap = {None:"http://psi.hupo.org/mi/mif300","xsi":"http://www.w3.org/2001/XMLSchema-instance"}
            globalVars.MIF = toNsString(nsmap)
            globalVars.ORDER_DICT = json.load(open(os.path.join(json_dir,"..","def300.json")))
            
        elif(ver=="mif254"):
            nsmap = {None:"http://psi.hupo.org/mi/mif","xsi":"http://www.w3.org/2001/XMLSchema-instance"}
            globalVars.MIF = toNsString(nsmap)
            globalVars.ORDER_DICT = json.load(open(os.path.join(json_dir,"..","def254.json")))
            
        xpath_ns_local = {"x":nsmap[None]}
        rootElem = etree.Element(globalVars.MIF+"entrySet",nsmap=nsmap)
        
        for attribkey,attribval in self.root.items():
            #root.attrib[attribkey] = attribval
            if not attribkey=="entries":
                rootElem.attrib[attribkey] = attribval
        
        #print(rootElem.attrib)
        for entry in self.root["entries"]:
            
            entryElem = etree.Element(globalVars.MIF+"entry")
            items = generateOrder("compactEntry", entry)
            #print(items)
            for key, val in items:
                #print(key)
                entryElem.append(genericMifGenerator(key,val))
            
            interactionList = entryElem.xpath("x:interactionList",namespaces=xpath_ns_local)[0]
            
            if(entryElem.xpath("x:abstractInteractionList",namespaces=xpath_ns_local)):
                abstractInteractionList = entryElem.xpath("x:abstractInteractionList",namespaces=xpath_ns_local)[0]
            
                for abstractInteraction in abstractInteractionList:
                    #print(abstractInteraction)
                    interactionList.append(abstractInteraction)
        
                entryElem.remove(abstractInteractionList)
            
            rootElem.append(entryElem)    
        
        return rootElem


    def toMoMif( self, ver='test' ):
        if(ver=="test"):
            nsmap = {None:"http://psi.hupo.org/mi/mif","xsi":"http://www.w3.org/2001/XMLSchema-instance"}
            attrib = {"level":"2","version":"5", "minorVersion":"4"}
            globalVars.MIF = toNsString(nsmap)
            json_dir = os.path.dirname(os.path.realpath(__file__))
            template = json.load(open(os.path.join(json_dir,"..","defTest.json")))

            return self.moGenericMifGenerator( nsmap, template, None, self.root,
                                               template['ExpandedEntrySet'],
                                               name="EntrySet", attrib=attrib )
        return None
    
    def moGenericMifGenerator(self, nsmap, template, dom, cdata, ctype, name=None, attrib=None ):

        self.UID = 1
        
        if name is not None:
            dom = etree.Element(globalVars.MIF + name,nsmap=nsmap)
        if attrib is not None:
            for a in attrib:
                dom.set(a,attrib[a])
            
        for cdef in ctype:            
            chldLst = self.moGenericMifElement( nsmap, template, None, cdata, cdef)
            for chld in chldLst:
                dom.append( chld )
            
        return dom
    
    def moGenericMifElement(self, nsmap, template, celem, cdata, cdef ):
        """Returns a list of elements to be added to the parent and decorates  
           parent with attributes. 
        """
        retLst = []
        if "wrap" in cdef:
            # add wrapper        

            wrapName = cdef["wrap"]
            wrapElem = etree.Element(globalVars.MIF + wrapName)        
        else:
            wrapElem = None
            
        if "value" not in cdef: # empty wrapper

            # wrapper contents definition
            wrappedTypes = template[cdef["type"]]
            
            empty = True # flag: will skip if nothing inside 
            for wtDef in wrappedTypes: # go over wrapper contents
                                
                if wtDef["value"] in cdata:  # check if data present 
                    wElemData = cdata[wtDef["value"]]
                    for wed in wElemData: # wrapper contents *must* be a list
                        empty = False # non empty contents
                        
                        if "name" in wtDef:
                            chldName = wtDef["name"]
                        else:
                            chldName = wtDef["value"]

                        # create content element inside a wrapper
                        chldElem = etree.Element(globalVars.MIF + chldName)   
                        wrapElem.append(chldElem)

                        # fill in according to element definition
                        for wtp in template[wtDef["type"]]:
                            wclLst = self.moGenericMifElement(nsmap, template,
                                                              chldElem, wed, wtp)                        
                            # add contents
                            for wcd in wclLst:
                                chldElem.append(wcd)
                                              
            if not empty:                                  
                return [wrapElem]
            else:
                return []
        
        if cdef["value"] =="$UID": #  generate next id
            self.UID += 1
            elemData = str(self.UID) 
        else:
            if cdef["value"] in cdata: # data from the record 
                elemData = cdata[ cdef["value"] ]
            else:               
                return [] # no data present: return empty list                   

        if "name" in cdef: # if present use name definition 
            elemName = cdef["name"]
        else:              # otherwise use the name of record field 
            elemName = cdef["value"]

            
        if isinstance( elemData, str):  # record field: text

            # attribute or text of the parent element

            if elemName.startswith('@'):  
                if elemName == "@TEXT" : # text of parent                
                    celem.text = str(elemData)
                else:                    # attribute of parent
                    celem.set(elemName[1:], str(elemData))                
            else: 
                if cdef["type"]=='$TEXT': # child element with text only                    
                    chldElem = etree.Element(globalVars.MIF + elemName)
                    chldElem.text = str( elemData )                

                    if wrapElem is not None: # add to wrapper (if present) 
                        wrapElem.append(chldElem)
                        return [wrapElem]
                    else: # otherwise add to return list            
                        retLst.append(chldElem)
            return retLst
                    
        if isinstance( elemData, dict): # record field: complex element 
            # convert single value to list
            elemData = [ elemData ]
            
        for celemData in elemData: # always a list here with one or more dict inside                    
            
            chldElem = etree.Element(globalVars.MIF + elemName)
            
            if cdef["type"]=='$TEXT': # text child element                 
                chldElem = etree.Element(globalVars.MIF + elemName)
                chldElem.text = str( elemData )
                retLst.append(chldElem)
            else: # complex content: build recursively
                contType = template[cdef["type"]]
                           
                for contDef in contType: # go over definitions
                    cldLst = self.moGenericMifElement(nsmap, template,
                                                      chldElem,
                                                      celemData,
                                                      contDef)                
                    for cld in cldLst:
                        chldElem.append(cld)
                        
                if wrapElem is not None:  # if present, add to wrapper
                    wrapElem.append(chldElem)
                else:                     #  otherwise add to return list    
                    retLst.append(chldElem)

        if wrapElem is not None:
            return [wrapElem]

        return retLst
    
    
class Entry():
    """Entry representation."""
    def __init__( self, root , id = 0):
        self.data = {}
        self.root = root
        self.id = id
    
    def __getitem__( self, id ):
        return self.getInteraction( id )

    @property
    def interaction(self):        
        return self.root[self.id]["interaction"] 

    def getInteraction( self, id, eid=None ):
        if eid is not None:
            return Interaction(self.root[eid],id)
        else:       
            return Interaction(self.root[self.id],id)
        
    def toMif254( self, parent, entry, curid ):
        if "source" in entry:
            sourceDom = etree.SubElement( parent, globalVars.MIF + "source" )
            curid = Source( self.root ).toMif254( sourceDom, entry["source"], curid )
            
        # interaction list only (this enforces expanded version) 
        if "interaction" in entry and len(entry["interaction"]) > 0:
            intnListDom = etree.SubElement( parent, globalVars.MIF + "interactionList" )

            for intn in entry["interaction"]:
                intnDom = etree.SubElement( intnListDom, globalVars.MIF + "interaction" )
                
                intnDom.set("id", str(curid))
                curid += 1
                curid = Interaction( self.root ).toMif254( sourceDom, intn,curid )
                
    def parseDom( self, dom ):

        for item in dom:
            tag = item.tag[globalVars.LEN_NAMESPACE:]            
            if tag == 'source':
                self.data["source"] = Source( self.data ).parseDom( item )
            
            elif tag == 'availabilityList':
                self.data[tag] = {}
                avlbElem = item.xpath( "x:availability", namespaces=globalVars.NAMESPACES )
                for avlb in avlbElem:
                    (cId, cAvlb) =  Availability( self.data ).parseDom(  avlb  )
                    self.data["availabilityList"][cId] = cAvlb
                
            elif tag == 'experimentList':
                self.data[tag] = {}
                expElem = item.xpath( "x:experimentDescription", namespaces=globalVars.NAMESPACES )            
                for exp in expElem:                    
                    (cId, cExp) =  Experiment( self.data ).parseDom( exp )                    
                    self.data["experimentList"][cId] = cExp
                
            elif tag == 'interactorList':
                self.data[tag] = {}
                intrElem = item.xpath( "x:interactor", namespaces=globalVars.NAMESPACES )
                for intr in intrElem:
                    (cId, cInt) =  Interactor( self.data ).parseDom( intr )
                    self.data["interactorList"][cId] = cInt 

            elif tag == 'interactionList':
               self.data[tag] = []
               intnElem = item.xpath( "x:interaction", namespaces=globalVars.NAMESPACES )
               for intn in intnElem:
                   (cId, cIntn) =  Interaction( self.data ).parseDom( intn )
                   self.data["interactionList"].append(cIntn)
               
               absIntnElem = item.xpath( "x:abstractInteraction", namespaces=globalVars.NAMESPACES )
               
               if absIntnElem:
                   self.data["abstractInteractionList"] = []
                   for absIntn in absIntnElem:
                       (cId, cIntn) =  Interaction( self.data ).parseDom( absIntn )
                       self.data["abstractInteractionList"].append(cIntn)
            
        
        return self.data

class Source():
    """Source representation."""
    def __init__( self, entry ):
        self.data={}
        self.entry = entry

    def parseDom( self, dom ):
        if(isinstance( dom, str)):
            record = etree.parse( dom )
            dom = record.xpath( "/x:entrySet/x:entry/x:source",
                                namespaces=globalVars.NAMESPACES )[0]        
       
        for item in dom:
            tag = modifyTag(item)
            self.data[tag] = genericSearch( self.entry, item )
            
        self.data["elementAttrib"]=attribToDict(dom.attrib) #sources have attributes
        
        return self.data
    
    def toMif254( self, parent, source, curid ):
        # build source content here
        return curid
    
class Experiment():
    """Experiment representation."""
    def __init__( self, entry ):
        self.data = {}
        self.entry = entry
        
    def parseDom( self, dom ):

        if(isinstance(dom, str)):
            record = etree.parse( dom )
            dom = record.xpath( "/x:entrySet/x:entry/x:experimentList/x:experiment",
                                namespaces=globalVars.NAMESPACES)[0]
        
        id = dom.xpath("./@id", namespaces=globalVars.NAMESPACES )
        
        for item in dom:
            tag = modifyTag(item)
            self.data[tag] = genericSearch( self.entry, item )

        #element with id attribute: return (id,data) tuple   
        return ( id[0], self.data )
        
class Interactor():
    """Interaction representation."""
    def __init__( self, entry ):
        self.data={}
        self.entry = entry

    def parseDom( self, dom ):

        if(isinstance(dom, str)):
            record = etree.parse(dom)
            dom = record.xpath( "/x:entrySet/x:entry/x:interactorList",
                                namespaces=globalVars.NAMESPACES)[0]
            
        id = dom.xpath("./@id", namespaces=globalVars.NAMESPACES )

        for item in dom:
            tag = modifyTag(item)
            self.data[tag] = genericSearch( self.entry, item )

        #element with id attribute: return (id,data) tuple   
        return ( id[0], self.data )

class Feature():
    """Feature representation."""
    def __init__( self, entry ):
        self.data={}
        self.entry = entry

    def parseDom( self, dom ):
            
        id = dom.xpath("./@id", namespaces=globalVars.NAMESPACES )

        for item in dom:
            tag = modifyTag(item)
            self.data[tag] = genericSearch( self.entry, item )

        #element with id attribute: return (id,data) tuple   
        return ( id[0], self.data )
    
class Interaction():
    """Interaction representation."""
    def __init__( self, entry, id=0 ):
        self.data={}
        self.entry = entry
        self.id=id
        
    @property
    def participant(self):
        return self.entry["interaction"][self.id]["participant"]

    @property
    def itype(self):
        return self.entry["interaction"][self.id]["interactionType"]

    @property
    def source(self):
        return self.entry["source"]


    def toMif254( self, parent, source, curid ):
        # build interaction content here
        return curid
    
    def parseDom( self, dom ):
        
        if(isinstance(dom, str)):
            record = etree.parse(dom)
            dom = record.xpath( "/x:entrySet/x:entry/x:interactionList",
                                namespaces=globalVars.NAMESPACES)[0]       
        
        idata = {}
        id = dom.xpath("./@id", namespaces=globalVars.NAMESPACES )
        imexId = dom.xpath("./@imexId",namespaces=globalVars.NAMESPACES)
        
        if(len(imexId)!=0):
            idata["imexId"] = imexId[0]
            
        for item in dom:
            tag = item.tag[globalVars.LEN_NAMESPACE:]
            if tag == "experimentList":

                idata[tag] = []

                # expanded form: <experimentDescription>...</experimentDescription>
                
                expElem = item.xpath( "x:experimentDescription", namespaces=globalVars.NAMESPACES )
                for exp in expElem:
                    
                    (cId, cExp) =  Experiment( self.entry ).parseDom( exp )
                    idata[tag].append( cExp )

                #  compact form: <experimentRef>...</experimentRef>
                    
                refElem = item.xpath( "x:experimentRef/text()", namespaces=globalVars.NAMESPACES )

                for ref in refElem:       

                    idata[tag].append( self.entry["experimentList"][ref] ) 

            elif tag == "participantList":
                idata[tag] = []
                prtElem = item.xpath( "x:participant", namespaces=globalVars.NAMESPACES )
                for prt in prtElem: 
                    (cId, cPrt) =  Participant( self.entry ).parseDom( prt )
                    idata[tag].append(cPrt)
                
            elif tag in ["modelled","intraMolecular","negative"]:
                idata[tag] = "bool"
                
            elif tag =="confidenceList":
                idata[tag] = "conf"  #skip fo rnow
                
            elif tag =="parameterList":
                idata[tag] = "param"  #skip for now
                
            elif tag=="cooperativeEffectList":
                idata[tag] = "coop"
                
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
    """Participant representation."""
    def __init__(self, entry):
        self.data = {}
        self.entry = entry
        
    def parseDom( self, dom ):
        # build participant here 
        pdata = {}
        id = dom.xpath("./@id", namespaces=globalVars.NAMESPACES )
        for item in dom:
            tag = item.tag[globalVars.LEN_NAMESPACE:]
            
            if tag == "interactorRef":
                refElem= item.xpath("text()")
                for ref in refElem:
                    pdata["interactor"] = self.entry["interactorList"][ref]
                    
            elif tag=="featureList":
               pdata[tag] = {}
               ftElem = item.xpath( "x:feature", namespaces=globalVars.NAMESPACES )
               for ft in ftElem:
                   (cId, cFt) =  Feature( self.data ).parseDom( ft )
                   pdata["featureList"][cId] = cFt
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
    """Names representation."""
    def __init__(self, entry ):
        self.entry = entry
        
    def parseDom( self, dom ):        
        ndata = {}
        for item in dom:
            tag = item.tag[globalVars.LEN_NAMESPACE:]
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
    """Xref representation."""
    def __init__( self, entry ):
        #self.data={}
        self.entry =entry
        
    def parseDom( self, dom ):
        #dom = dom.xpath(".",namespaces=globalVars.NAMESPACES)[0]
        #self.data = genericSearch( self.entry, dom)
        xdata = {"refInd":{}}
        for item in dom:
            tag = item.tag[globalVars.LEN_NAMESPACE:]
            if tag == "primaryRef":
                attribDict = attribToDict(item.attrib)
                db_id = item.attrib.get("db")+":"+item.attrib.get("id")
                xdata["primaryRef"] = attribDict
                xdata["refInd"][db_id] = attribDict
                    
                
            elif tag == "secondaryRef":
                db_id = item.attrib.get("db")+":"+item.attrib.get("id")
                attribDict = attribToDict(item.attrib)
                if not "secondaryRef" in xdata.keys():
                    xdata["secondaryRef"] = []
                    
                xdata["secondaryRef"].append(attribDict)
                xdata["refInd"][db_id] = attribDict
                
        return (xdata)
                    
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
    """Attribute representation."""
    def __init__( self, entry ):
        #self.data = []
        self.entry = entry
        
    def parseDom( self, dom ):
        attribdata = []
        attrDom = dom.xpath("x:attribute",namespaces=globalVars.NAMESPACES)
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
    """Availability representation."""
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
    """CvTerm representation - CvTerms contain names and xref elements only."""
    def __init__(self, entry):
        self.entry = entry
        
    def parseDom( self, dom ):
        cvdata = {}
        for item in dom:
            tag = item.tag[globalVars.LEN_NAMESPACE:]
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
    """ListedElement representation - ListedElements contain children as items in a list rather than key-value pairs in a dictionary."""
    def __init__(self,entry):
        self.entry = entry
    
    def parseDom( self, dom ):
        eldata = []
        for item in dom:
            #print(item.tag)
            eldata.append(genericSearch(self.entry,item))
            
        return eldata
    



