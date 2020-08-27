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

import pymex


#------------------------------ CLASSES ------------------------------------------------------
    

class MifParser():
    """Parses a mif file associated with a filename. Saves to Mif254Record object."""

    def __init__(self,debug=False):
        self.debug = debug
        
    def parse( self, filename, ver ):       
        #mif = MifRecord()
        mif = pymex.mif.Record()
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
        
   
class Source():
    """Source representation."""   
    def __init__( self, entry ):
        self.data={}
        self.entry = entry
    
class Experiment():
    """Experiment representation."""
    def __init__( self, entry ):
        self.data = {}
        self.entry = entry
        
class Interactor():
    """Interaction representation."""
    def __init__( self, entry ):
        self.data={}
        self.entry = entry

class Feature():
    """Feature representation."""
    def __init__( self, entry ):
        self.data={}
        self.entry = entry
    
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
    
class Participant():
    """Participant representation."""
    def __init__(self, entry):
        self.data = {}
        self.entry = entry
    
class Names():
    """Names representation."""
    def __init__(self, entry ):
        self.entry = entry
    
class Xref():
    """Xref representation."""
    def __init__( self, entry ):
        #self.data={}
        self.entry =entry
        
class Attribute():
    """Attribute representation."""
    def __init__( self, entry ):
        #self.data = []
        self.entry = entry
        
class Availability():
    """Availability representation."""
    def __init__( self, entry ):
        self.entry = entry
        
class CvTerm():
    """CvTerm representation - CvTerms contain names and xref elements only."""
    def __init__(self, entry):
        self.entry = entry

class ListedElement():
    """ListedElement representation - ListedElements contain children as items in a list rather than key-value pairs in a dictionary."""
    def __init__(self,entry):
        self.entry = entry



