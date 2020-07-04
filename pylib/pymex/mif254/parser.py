# -*- coding: utf-8 -*-
"""
Created on Mon Jun 29 13:56:57 2020

@author: andrei
"""


# -*- coding: utf-8 -*-
from lxml import etree
import json
from collections import defaultdict

NAMESPACES = {"x":"http://psi.hupo.org/mi/mif"}
LEN_NAMESPACE = len(NAMESPACES["x"])+2 #because of the two brackets around the text
IDENTIFIED_LISTED_ELEMENTS = ["interactor","experimentDescription","participant","interaction","hostOrganism"] #these need to be hashed by ID in the recursive case

def attribToDict(attrib): #Converts an ElementTree attrib object to a python dictionary.
    pyDict = {}
    for item in attrib:
        pyDict[item] = attrib.get(item)
    return pyDict

def genericSearch(root): #Recursive search through element tree
    data = {}
    #print(root)
    for item in root:
        tag = item.tag[LEN_NAMESPACE:]
        if item.text and len(item)==0:
            if tag=="alias" or tag=="attribute":
                print('hi')
                modifiedAttrib = attribToDict(item.attrib)
                modifiedAttrib["text"] = item.text
                if tag in data.keys():

                    data[tag].append(modifiedAttrib)
                else:
                    data[tag] = [modifiedAttrib]        
            else:
                data[tag] = {}
                data[tag]["text"] = item.text
                data[tag]["elementAttrib"]=attribToDict(item.attrib)
                
        elif item.attrib and len(item)==0: #pretty much all items have 
            if tag=="secondaryRef": #secondaryRef IDs are unique,so we hash by that.
                tag += " id=" + item.attrib.get("id")
                
            data[tag] = {}
            data[tag]["elementAttrib"]=attribToDict(item.attrib)
            #print('b')
        elif tag == "names":
            names = Names()
            data["names"] = names.build(root)
            #print('c')
        elif tag == "xref":
            xref = XRef()
            data["xref"] = xref.build(root)
            #print('d')
        elif tag == "attributeList":
            attributeList = AttributeList()
            data["attributeList"] = attributeList.build(root)
            #print('e')
        else:
            if tag in IDENTIFIED_LISTED_ELEMENTS:
                if tag=="hostOrganism":
                    tag+= " ncbiTaxId=" + item.attrib.get("ncbiTaxId")
                else:
                    tag+= " id=" + item.attrib.get("id")
            data[tag] = genericSearch(item)
            if item.attrib:
                data[tag]["elementAttrib"]=attribToDict(item.attrib)
            #print('f')
        
        
    return data

class Mif254Record: #Stores mif files as python dictionary of dictionaries.
    # something else
    def __init__(self):
        self.data=[]
    
    def build(self,filename):
        
        record = etree.parse(filename)
        entries = record.xpath("/x:entrySet",namespaces=NAMESPACES)
        if entries:
            for entry in entries:
                entryElem = Entry()
                entryElem.build(entry)
                self.data.append(entryElem)
            

class Mif254Parser: #Parses a mif file associated with a filename. Saves to Mif254Record object.
    def __init__(self,debug=False):
        self.debug = debug
                    

    def parse(self, filename):
        mif = Mif254Record()
        mif.build(filename)
        return mif

        
class Entry():
    def __init__(self):
        self.data = {}
        
    def build(self,root):
        root = root.xpath("x:entry",namespaces=NAMESPACES)[0]
        source = Source()
        experiments = Experiments()
        interactors = Interactors()
        interactions = Interactions() 
        self.data["source"] = source.build(root)
        self.data["experiments"] = experiments.build(root)
        self.data["interactors"] = interactors.build(root)
        self.data["interactions"] = interactions.build(root)

class Source():
    def __init__(self):
        self.data={}
    
    def build(self,root):
        root = root.xpath("x:source",namespaces=NAMESPACES)[0]
        return genericSearch(root)

class Experiments():
    def __init__(self):
        self.data={}
    
    def build(self,root):
        root = root.xpath("x:experimentList",namespaces=NAMESPACES)[0]
        return genericSearch(root)

class Interactors():
    def __init__(self):
        self.data={}
    
    def build(self,root):
        root = root.xpath("x:interactorList",namespaces=NAMESPACES)[0]
        return genericSearch(root)

class Interactions():
    def __init__(self):
        self.data={}
    
    def build(self,root):
        root = root.xpath("x:interactionList",namespaces=NAMESPACES)[0]
        return genericSearch(root)
    
class Names():
    def __init__(self):
        self.data={}
        
    def build(self,root):
        root = root.xpath("x:names",namespaces=NAMESPACES)[0]
        return genericSearch(root)     
    
class XRef():
    def __init__(self):
        self.data={}
    def build(self,root):
        root = root.xpath("x:xref",namespaces=NAMESPACES)[0]
        return genericSearch(root)
                
class AttributeList():
    def __init__(self):
        self.data={}
    def build(self,root):
        root = root.xpath("x:attributeList",namespaces=NAMESPACES)[0]
        return genericSearch(root)
