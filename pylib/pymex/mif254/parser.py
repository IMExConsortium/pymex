# -*- coding: utf-8 -*-
"""
Created on Mon Jun 29 13:56:57 2020

@author: andrei
"""


# -*- coding: utf-8 -*-
from lxml import etree
from abc import ABC
import sys

NAMESPACES = {"x":"http://psi.hupo.org/mi/mif"}
LEN_NAMESPACE = len(NAMESPACES["x"])+2 #because of the two brackets around the text

def genericSearch(root):
    data = {}
    #print(root)
    for item in root:
        #print(item.tag)
        if item.text and len(item)==0:
            data[item.tag[LEN_NAMESPACE:]] = item.text
            #print('a')
        elif item.attrib and len(item)==0:
            data[item.tag[LEN_NAMESPACE:]] = item.attrib
            #print('b')
        elif item.tag[LEN_NAMESPACE:] == "names":
            names = Names()
            data["names"] = names.build(root)
            #print('c')
        elif item.tag[LEN_NAMESPACE:] == "xref":
            xref = XRef()
            data["xref"] = xref.build(root)
            #print('d')
        elif item.tag[LEN_NAMESPACE:] == "attributeList":
            attributeList = AttributeList()
            data["attributeList"] = attributeList.build(root)
            #print('e')
        else:
            data[item.tag[LEN_NAMESPACE:]] = genericSearch(item)
            #print('f')
        
    return data

class Mif254Record:
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
            

class Mif254Parser:
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
        

     


