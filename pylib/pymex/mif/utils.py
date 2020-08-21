# -*- coding: utf-8 -*-
"""
Created on Wed Aug 19 02:05:33 2020

@author: andrei
"""

#-------------------- IMPORTS -----------------------------------------------------------------------
 
# -*- coding: utf-8 -*-
from lxml import etree
import mif.globalVars as globalVars

#-------------------------------- UTILITIES --------------------------------------------------
def isListedElement(item):
    """ Does this element need to be parsed as a ListedElement?"""
    return item.tag.endswith("List")
    
def modifyTag(item): 
    """ Modifies tag of an item if necessary."""
    tag = item.tag[globalVars.LEN_NAMESPACE:]
    return tag
    
def isCvTerm(dom):
    """ Determines whether or not a given ElementTree element is a CvTerm."""

    elemList = list(dom)
    return (len(elemList) == 2 and elemList[0].tag[globalVars.LEN_NAMESPACE:] == "names" and elemList[1].tag[globalVars.LEN_NAMESPACE:] == "xref")

def attribToDict( attrib ):
    """Converts an ElementTree attrib object to a python dictionary."""

    pyDict = {}
    for item in attrib:
        pyDict[item] = attrib.get(item)
    return pyDict


    
#----------------------------TO MIF UTILITIES-------------------------------------------------

def toNsString(ns): 
    """Converts namespace to string prefix for element tags."""
    mif_ns = ns[None]
    mifstr = "{%s}" % mif_ns
    return mifstr

def namesOrder(orderList):
    """Generates a list of strings that determine the order of children in an Element according to MIF schema."""
    namesOrderList = []
    for item in orderList:
        if("wrap" in item.keys()):
            namesOrderList.append(item["wrap"])
        elif("value" in item.keys()):
            namesOrderList.append(item["value"])
            
    return namesOrderList

def generateOrder(key, value):
    """Orders children of an element according to namesOrder if key is present in the MIF schema JSON."""
    if(key in globalVars.ORDER_DICT.keys()):
        items = [(s,value[s]) for s in namesOrder(globalVars.ORDER_DICT[key]) if s in value.keys()]
        #print((key,[item[0] for item in items]))
    else:
        items = value.items()
    
    return items
        
def isTextElement(text):
    """Determines if 'text' argument should be parsed as a etree Element containing text."""
    return (isinstance(text,str) or (isinstance(text,dict) and "value" in text.items()))
    
def buildTextElement(name,text): 
    """Builds a key-value pair (name,text) into an etree Element containing text."""
    root = etree.Element(name)
    
    
    
    if(isinstance(text,dict)):
        items = generateOrder(name, text)
        for textkey, textval in items:
            if(textkey=="value"):
                root.text = textval
            else:
                root.attrib[textkey] = textval   
                    
    elif(isinstance(text,str)):
        root.text=text
        
    return root
                
   
def genericMifGenerator(rawkey,value): #root is a value in key value pair 
    "Recursive MIF serializer from MifRecord object key-value pairs."
    if not globalVars.MIF in rawkey: #add the namespace
        key = globalVars.MIF+rawkey
    else:
        key = rawkey
        
    root = etree.Element(key)
    if(isinstance(value,tuple)):
        val = value[1]
    else:
        val = value.copy()
        
    if((rawkey in ["experimentList","interactorList","availabilityList","featureList"]) and isinstance(val,dict)):
        for expkey, expval in val.items():
            
            if rawkey=="experimentList":
                childName = "experimentDescription"
                
            else:
                childName = key[:-4]
            childExp = genericMifGenerator(childName,expval)
            
            childExp.attrib["id"] = str(globalVars.ID_NUM)
            globalVars.ID_NUM+=1
            
            if(rawkey)=="interactionList" and "imexId" in expval.keys() : #interactions have IMEX IDs
                childExp.attrib["imexId"] = expval["imexId"]
                
            #print(rawkey,expkey)
            

            #print(globalVars.ID_NUM)
            root.append(childExp)
    
    elif(rawkey=="participantList"):
        

        for participant in val:

            items = generateOrder("participant", participant)
            partElem = etree.Element("participant")   
            
            partElem.attrib["id"] = str(globalVars.ID_NUM)
            globalVars.ID_NUM+=1
            
            #print(rawkey,participantID)

            for partkey, partval in items:
                #print(partkey)
                if(partkey=="interactor"):
                    
                    childExp = genericMifGenerator(partkey,partval)
                        
                    childExp.attrib["id"] = str(globalVars.ID_NUM)
                    globalVars.ID_NUM+=1
                        
                    partElem.append(childExp)
                else:
                    partElem.append(genericMifGenerator(partkey,partval))
            root.append(partElem)
            
    elif (rawkey=="attributeList"):
        for item in val:
            root.append(buildTextElement(globalVars.MIF+"attribute",item))        
            
    elif(rawkey=="names"): #names is a special case
        items = generateOrder(rawkey, val)
        for namekey,nameval in val.items(): 
            #print(namekey)
            if(isinstance(nameval,str)):
                root.append(buildTextElement(globalVars.MIF+namekey,nameval))
            else: #nameval is a list of aliases
                for alias in nameval:
                    root.append(buildTextElement(globalVars.MIF+namekey,alias))
                    
    elif(rawkey=="xref"):
        items = generateOrder(rawkey, val)
        for xkey, xval in val.items():
            #print(xkey)
            if(xkey=="refInd"):
                continue    
            elif(isinstance(xval,dict)): #primaryRef
                root.append(buildTextElement(globalVars.MIF+xkey,xval))
            else: #secondaryRef
                for secref in xval:
                    root.append(buildTextElement(globalVars.MIF+xkey,secref))    
                    
    elif(isinstance(val,dict)):
        parseChildren(root,val,rawkey)
             
    elif(isinstance(val,list)):
        for item in val:
                
            if key.endswith("List"):
                    
                if(rawkey=="bindingFeatureList"):
                    modifiedKey = globalVars.MIF+"bindingFeatures"
                else:
                    modifiedKey = key[:-4]
                childElem = etree.Element(modifiedKey)
                
                if(rawkey in ["interactionList","abstractInteractionList"]):
                    childElem.attrib["id"] = str(globalVars.ID_NUM)
                    globalVars.ID_NUM+=1
            else:
                childElem = etree.Element(key)
            root.append(childElem)
            parseChildren(childElem,item,rawkey)
            
    
    return root      

def parseChildren(root, item, key): #when recursively parsing through these objects, we have to look at children because their contents may have to be added back to the root
    
    items = generateOrder(key, item)
    
    for subkey, subval in items:
        if(subkey=="elementAttrib"):
            for attribkey, attribval in subval.items():
                root.attrib[attribkey] = attribval
                
        elif(subkey=="ncbiTaxId"):
            root.attrib[subkey] = subval
            
        elif(isTextElement(subval)):
            root.append(buildTextElement(subkey,subval))
                
        else:
            #print(subkey)
            root.append(genericMifGenerator(subkey,subval))     
