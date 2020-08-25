# -*- coding: utf-8 -*-
"""
Created on Mon Jun 29 13:56:57 2020
@author: andrei
"""

from lxml import etree as ET
import json
from xml.dom import minidom
import os

import pymex

from mif.utils import *
import mif.globalVars as globalVars

class Record():
    """MIF record representation."""

    def __init__(self, root=None):
        if root is not None:
            self.root = root
        else:
            self.root = {}
    
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

    def parseMif(self, filename, ver="mif254", debug=False):

        if(ver=="mif300"):
            globalVars.NAMESPACES = {"x":"http://psi.hupo.org/mi/mif300"}
            
        elif(ver=="mif254"):
            globalVars.NAMESPACES = {"x":"http://psi.hupo.org/mi/mif"}

            #load parserdefinition

            json_dir = os.path.dirname( os.path.realpath(__file__) )
            template = json.load( open( os.path.join(json_dir, "defParse254.json") ) )
     
        globalVars.LEN_NAMESPACE = len(globalVars.NAMESPACES["x"])+2
        
        recordTree = ET.parse( filename )
        rootElem = recordTree.getroot()
        
        self.genericParse( template, self.root, [] , rootElem, debug )
        return self

    def genericParse(self, template, rec, rpath, elem, wrapped=False, debug=False):
        
        tag = modifyTag( elem )
        
        #find corresponding template
        if tag in template:
            ttempl = template[tag]
        else:
            ttempl = template["*"] 

        if debug:
            print("\nTAG", tag, wrapped, len(rpath) )
            print(" TTEM", ttempl)
        
        if elem.getparent() is not None:
            parentElem = elem.getparent()
            if wrapped:
                if  parentElem.getparent() is not None:
                    parentElem = parentElem.getparent()
                else:
                    parentElem = None            
        else:
            parentElem = None
            
        if parentElem is not None:
            parentTag = modifyTag( parentElem )
            if debug:
                print(" PAR", parentTag )
            
        else:
            parentTag = None
            if debug:
                print("PAR:  ROOT ELEM !!!")

        if parentTag is not None and parentTag in ttempl:
            ctempl = ttempl[parentTag]
        else:
            ctempl = ttempl["*"]
        if debug:
            print("  CTEMPL", ctempl )

        # find wrap flag
        if "wrapper" in ctempl and ctempl["wrapper"] is not None:
            cwrap = ctempl["wrapper"]
        else:
            #default
            cwrap = template["*"]["*"]["wrapper"]            
        if debug:
            print( "  CWRAP ", cwrap )

        if cwrap:
            for cchld in elem:
                if debug:
                    print("  CHLD",cchld.tag);

                self.genericParse( template, rec, rpath, cchld, wrapped =True)
                if debug:
                    print( json.dumps(self.root, indent=2) )                
            return 
        
        # find current key:        
        if "name" in ctempl and ctempl["name"] is not None:
            ckey = ctempl["name"]
        else:
            ckey = tag
        
        # find complex flag
        if "complex" in ctempl and ctempl["complex"] is not None:
            ccomplex = ctempl["complex"]        
        else:            
            #default
            ccomplex = template["*"]["*"]["complex"]

        # test if reference
        rtgt  = None
        if "reference" in ctempl and ctempl["reference"] is not None:
             rtgt = ctempl["reference"]
        else:
            #default
            rtgt = template["*"]["*"]["reference"]

        # find current store type (direct/list/index)
        if "store" in ctempl and ctempl["store"] is not None:
            cstore = ctempl["store"]
        else:
            #default
            cstore = template["*"]["*"]["store"]
             
        if debug:
            print( "  CKEY  ", ckey )
            print( "  CCMPLX", ccomplex )
            print( "  CSTORE", cstore )
            print( "  CREFTG", rtgt )
            
        if rtgt is not None:
            # add referenced data
            # elem.text: a reference
            # rtgt     : path to referenced dictionary along current path
            #            within record data structure  

            stgt = rtgt.split('/')
            for i in range(1,len(stgt)):
                if stgt[i] in rpath[i-1]:
                    pass
                else:
                    break

            lastmatch = rpath[i-2][stgt[i-1]]
            if cstore == "list":
                if ckey not in rec:
                    rec[ckey] = []
                rec[ckey].append( lastmatch[stgt[i]][elem.text] )
            elif cstore == "direct":
                rec[ckey] = lastmatch[stgt[i]][elem.text]
                
        else:
            # build/add current value
            cvalue = None
            if ccomplex:
                cvalue = {}
                if elem.text:
                    val = str(elem.text).strip()
                    if len(val) > 0:
                        cvalue["value"] = val
            else:
                cvalue = str( elem.text )

            if cstore  == "direct":
                rec[ckey] = cvalue
            elif cstore == "list": 
                if ckey not in rec:
                    rec[ckey] = []
                rec[ckey].append(cvalue)
            elif cstore == "index":
                if ckey not in rec:
                    rec[ckey] = {}

                if "ikey" in ctempl and ctempl["ikey"] is not None:
                    ikey = ctempl["ikey"]
                else:
                    #default
                    ikey = template["*"]["*"]["ikey"]

                if ikey.startswith("@"):
                    iattr= ikey[1:]
                    ikeyval = elem.get(iattr)
                
                    if ikeyval is not None:                
                        rec[ckey][ikeyval] = cvalue        
                   
            # parse elem contents
                
            # add dom attributes
            for cattr in elem.attrib:
                cvalue[cattr] = str( elem.attrib[cattr] )

            cpath = []
            for p in rpath:
                cpath.append(p)
            
            cpath.append( {tag: cvalue })
                
            for cchld in elem:
                if debug:
                    print("  CHLD", cchld.tag);
                self.genericParse( template, cvalue, cpath, cchld)
            if debug:
                print( json.dumps(self.root, indent=2) )
        return
        
    def parseDom( self, filename , ver):
        """Builds a MifRecord object from an MIF XML file."""
        if(ver=="mif300"):
            globalVars.NAMESPACES = {"x":"http://psi.hupo.org/mi/mif300"}
            
        elif(ver=="mif254"):
            globalVars.NAMESPACES = {"x":"http://psi.hupo.org/mi/mif"}
        
        globalVars.LEN_NAMESPACE = len(globalVars.NAMESPACES["x"])+2
        
        record = ET.parse( filename )
        entrySet = record.xpath("/x:entrySet",namespaces=globalVars.NAMESPACES)
        for key, val in entrySet[0].attrib.items():
            self.root[key] = val
        entries = record.xpath( "/x:entrySet/x:entry", namespaces=globalVars.NAMESPACES )
        for entry in entries:
            entryElem = pymex.mif.Entry( self.root )
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
        rootElem = ET.Element(globalVars.MIF+"entrySet",nsmap=nsmap)
        
        for attribkey,attribval in self.root.items():
            #root.attrib[attribkey] = attribval
            if not attribkey=="entries":
                rootElem.attrib[attribkey] = attribval
        
        #print(rootElem.attrib)
        for entry in self.root["entries"]:
            
            entryElem = ET.Element(globalVars.MIF+"entry")
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
        """Builds MIF elementTree from a Record object."""
        
        if(ver=="test"):
            nsmap = {None:"http://psi.hupo.org/mi/mif", "xsi":"http://www.w3.org/2001/XMLSchema-instance"}
        
            globalVars.MIF = toNsString( nsmap )
            json_dir = os.path.dirname( os.path.realpath(__file__) )
            template = json.load( open( os.path.join(json_dir, "defMif254.json") ) )

            return self.moGenericMifGenerator( nsmap, template, None, self.root["entrySet"],
                                               template['ExpandedEntrySet'] )
        return None
    
    def moGenericMifGenerator(self, nsmap, template, dom, cdata, ctype):
        """Returns DOM representation of the MIF record defined by the template.
        """
        
        self.UID = 1
        
        name = template["@ROOT"]["name"]
        if "attribute" in template["@ROOT"]:
            attrib = template["@ROOT"]["attribute"]
        else:
            attrib = None
            
        dom = ET.Element(globalVars.MIF + name,nsmap=nsmap)
        if attrib is not None:
            for a in attrib:
                dom.set(a,attrib[a])
            
        for cdef in ctype:            
            chldLst = self.moGenericMifElement( nsmap, template, None, cdata, cdef)
            for chld in chldLst:
                dom.append( chld )
            
        return dom
    
    def moGenericMifElement(self, nsmap, template, celem, cdata, cdef ):
        """Returns a list of DOM elements to be added to the parent and/or decorates  
           parent with attributes and text value . 
        """
        retLst = []
        if "wrap" in cdef:
            # add wrapper        

            wrapName = cdef["wrap"]
            wrapElem = ET.Element(globalVars.MIF + wrapName)        
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
                        chldElem = ET.Element(globalVars.MIF + chldName)   
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
                    chldElem = ET.Element(globalVars.MIF + elemName)
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
            
            chldElem = ET.Element(globalVars.MIF + elemName)
            
            if cdef["type"]=='$TEXT': # text child element                 
                chldElem = ET.Element(globalVars.MIF + elemName)
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
    



