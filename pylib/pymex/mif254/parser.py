# -*- coding: utf-8 -*-
"""
Created on Mon Jun 29 13:56:57 2020

@author: andrei
"""

# -*- coding: utf-8 -*-
from lxml import etree
import json

NAMESPACES = {"x":"http://psi.hupo.org/mi/mif"}
LEN_NAMESPACE = len(NAMESPACES["x"])+2 #because of the two brackets around the text
IDENTIFIED_LISTED_ELEMENTS = ["interactor","experimentDescription","participant","interaction","hostOrganism"] #these need to be hashed by ID in the recursive case


def attribToDict(attrib): #Converts an ElementTree attrib object to a python dictionary.
    pyDict = {}
    for item in attrib:
        pyDict[item] = attrib.get(item)
    return pyDict

def genericSearch( entry, dom  ): #Recursive search through element tree
    data = {}
    for item in dom:        
        tag = item.tag[LEN_NAMESPACE:]
        #print(tag)
        if item.text and len(item)==0:
            if tag=="alias" or tag=="attribute":
                modifiedAttrib = attribToDict(item.attrib)
                modifiedAttrib["text"] = item.text
                if tag in data.keys():

                    data[tag].append(modifiedAttrib)
                else:
                    data[tag] = [modifiedAttrib]

            elif tag == "experimentRef":
                data["experiment"] = entry["experiment"][item.text.strip()]                
                
            else:
                data[tag] = {}
                data[tag]["text"] = item.text
                data[tag]["elementAttrib"]=attribToDict(item.attrib)
        
        elif item.attrib and len(item)==0: #pretty much all items have 
            if tag=="secondaryRef": #secondaryRef IDs are unique,so we hash by that.
                tag += " id=" + item.attrib.get("id")                
            data[tag] = {}
            data[tag]["elementAttrib"]=attribToDict(item.attrib)
            #print(tag,'b')
        elif tag == "names":
            names = Names( entry )
            data["names"] = names.build( item )
            #print(tag,'c')
        elif tag == "xref":
            xref = Xref( entry )
            data["xref"] = xref.build( item )
            #print(tag,'d')
        elif tag == "attributeList":
            #attributeList = AttributeList( entry )
            data["attribute"] = Attribute(entry).build( item )
            print(tag,'e')
        else:
            if tag in IDENTIFIED_LISTED_ELEMENTS:
                if tag=="hostOrganism":
                    tag+= " ncbiTaxId=" + item.attrib.get("ncbiTaxId")
                else:
                    tag+= " id=" + item.attrib.get("id")
            if tag == 'experimentDescription':                
                data[tag] = genericSearch( entry, item)
                if item.attrib:
                    data[tag]["elementAttrib"]=attribToDict(item.attrib)
            #print(tag,'f')
    
    return data

class Mif254Parser: #Parses a mif file associated with a filename. Saves to Mif254Record object.
    def __init__(self,debug=False):
        self.debug = debug
        
    def parse( self, filename ):
        mif = Mif254Record()
        mif.build( filename )
        return mif

class Mif254Record: #Stores mif files as python dictionary of dictionaries.
    # something else
    def __init__(self):
        self.root = []
    
    def build( self, filename ):
        
        record = etree.parse( filename )
        entries = record.xpath( "/x:entrySet/x:entry", namespaces=NAMESPACES )
        for entry in entries:
            entryElem = Entry( self.root )
            self.root.append( entryElem.build( entry ) )
    
    def toJson(self):
        return json.dumps(self.root, indent=2)
        
class Entry():
    def __init__( self, root ):
        self.data = {}
        self.root = root
        
    def build( self, dom ):

        for item in dom:
            tag = item.tag[LEN_NAMESPACE:]            
            if tag == 'source':
                self.data["source"] = Source( self.data ).build( item )
                
            elif tag == 'experimentList':
                self.data["experiment"] = {}
                expElem = item.xpath( "x:experimentDescription", namespaces=NAMESPACES )            
                for exp in expElem:                    
                    (cId, cExp) =  Experiment( self.data ).build( exp )                    
                    self.data["experiment"][cId] = cExp
                
            elif tag == 'interactorList':
                self.data["interactor"] = {}
                intrElem = item.xpath( "x:interactor", namespaces=NAMESPACES )
                for intr in intrElem:
                    (cId, cInt) =  Interactor( self.data ).build( intr )
                    print(cId)
                    self.data["interactor"][cId] = cInt 

            elif tag == 'interactionList':
               self.data["interaction"] = []
               intnElem = item.xpath( "x:interaction", namespaces=NAMESPACES )
               for intn in intnElem:
                   (cId, cIntn) =  Interaction( self.data ).build( intn )
                   self.data["interaction"].append( cIntn )
                    
            elif tag == 'availabilityList':
                self.data["availability"] = {}
                avlbElem = item.xpath( "x:availability", namespaces=NAMESPACES )
                for avlb in avlbElem:
                    (cId, cAvlb) =  Availability( self.data ).build( intn )
                    self.data["availability"][cId] = cAvlb
        
        return self.data

class Source():
    def __init__( self, entry ):
        self.data={}
        self.entry = entry

    def build( self, dom ):
        if(isinstance( dom, str)):
            record = etree.parse( dom )
            dom = record.xpath( "/x:entrySet/x:entry/x:source",
                                namespaces=NAMESPACES )[0]        
       
        self.data = genericSearch( self.entry, dom )
        return self.data

class Experiment():
    def __init__( self, entry ):
        self.data = {}
        self.entry = entry
        
    def build( self, dom ):    
        id = dom.xpath("./@id", namespaces=NAMESPACES )    
        data =  genericSearch( self.entry, dom )
        return ( id[0], data )
        
class Interactor():
    def __init__(self, entry):
        self.data={}
        self.entry = entry

    def build( self, dom ):
        id = dom.xpath("./@id", namespaces=NAMESPACES )
        data = genericSearch( self.entry, dom )
            
        return ( id[0], data )

class Interaction():
    def __init__(self,entry):
        self.data={}
        self.entry = entry
    
    def build( self, dom ):
        idata = {}
        id = dom.xpath("./@id", namespaces=NAMESPACES )
        for item in dom:
            print(item)
            tag = item.tag[LEN_NAMESPACE:]
            print(tag)
            if tag == "names":                          
                idata["names"] = Names(self.entry).build( item )    

            elif tag == "xref":                           
                idata["xref"] = Xref(self.entry).build( item )

            elif tag == "experimentList":

                idata["experiment"] = []

                # expanded form: <experimentDescription>...</experimentDescription>
                
                expElem = item.xpath( "x:experimentDescription", namespaces=NAMESPACES )
                for exp in expElem:
                    
                    (cId, cExp) =  Experiment( self.data ).build( exp )
                    idata["experiment"].append( cExp )

                #  compact form: <experimentRef>...</experimentRef>
                    
                refElem = item.xpath( "x:experimentRef/text()", namespaces=NAMESPACES )

                for ref in refElem:                
                    idata["experiment"].append( self.entry["experiment"][ref] ) 

            elif tag == "participantList":
                idata["participant"] = []
                prtElem = item.xpath( "x:participant", namespaces=NAMESPACES )
                for prt in prtElem:                
                    (cId, cPrt) =  Participant( self.data ).build( prt )
                    idata["participant"].append( cPrt )

            elif tag == "interactionType":
                if "interactionType" not in  idata:
                    idata["interactionType"] = []
                idata["interactionType"].append( CvTerm(self.entry).build( item ) )
                
            elif tag in ["modelled","intraMolecular","negative"]:
                idata[tag] = "bool"
                
            elif tag =="confidenceList":
                idata["confidence"] = "conf"
                
            elif tag =="parameterList":
                idata["parameter"] = "param"
                
            elif tag =="attributeList":
                idata["attribute"] = Attribute(self.entry).build( item )
                    
        return ( id[0], idata )
    
class Names():
    def __init__(self, entry ):
        self.data={}
        self.entry = entry
        
    def build( self, dom ):
        dom = dom.xpath("*",namespaces=NAMESPACES)[0]
        self.data = genericSearch( self.entry, dom)
        return self.data    
    
class Xref():
    def __init__( self, entry ):
        self.data={}
        self.entry =entry
        
    def build( self, dom ):
        dom = dom.xpath(".",namespaces=NAMESPACES)[0]
        self.data = genericSearch( self.entry, dom)
        return self.data

class Attribute():
    def __init__( self, entry ):
        self.data = []
        self.entry =entry
        
    def build( self, dom ):
        
        attrDom = dom.xpath("x:attribute",namespaces=NAMESPACES)
        for attr in attrDom: 
            self.data.append("attr")
        return self.data
        
class Availability():
    def __init__( self, entry ):
        self.data = []
        self.entry = entry
        
    def build( self, dom ):
        dom = dom.xpath("x:availabilityList/x:availability",namespaces=NAMESPACES)
        if dom:        
            self.data = genericSearch( self.entry, dom )
        return self.data
        
class CvTerm():
    def __init__(self, entry):
        self.data = {}
        self.entry = entry
        
    def build( self, dom ):
        # build cvterm here 
        
        return self.data
        
class Participant():
    def __init__(self, entry):
        self.data = {}
        self.entry = entry
        
    def build( self, dom ):
        # build participant here 
        pdata = {}
        id = dom.xpath("./@id", namespaces=NAMESPACES )
        
        return (id[0], pdata )
        
    
