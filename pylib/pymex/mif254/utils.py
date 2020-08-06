#-------------------------------- GLOBALS -------------------------------------------------------------
NAMESPACES = {"x":"http://psi.hupo.org/mi/mif"}
LEN_NAMESPACE = len(NAMESPACES["x"])+2 #because of the two brackets around the text 
LISTED_ELEMENTS = ["hostOrganismList","experimentalRoleList","experimentalPreparationList","featureList","featureRangeList","attributeList"] #we no longer have a need for identified listed elements.
#-------------------------------- UTILITIES --------------------------------------------------
def modifyTag(item): 
    """ Modifies tag of an item if necessary."""
    tag = item.tag[LEN_NAMESPACE:]
    return tag
    
def isCvTerm(dom):
    """ Determines whether or not a given ElementTree element is a CvTerm."""

    elemList = list(dom)
    return (len(elemList) == 2 and elemList[0].tag[LEN_NAMESPACE:] == "names" and elemList[1].tag[LEN_NAMESPACE:] == "xref")

def attribToDict( attrib ):
    """Converts an ElementTree attrib object to a python dictionary."""

    pyDict = {}
    for item in attrib:
        pyDict[item] = attrib.get(item)
    return pyDict

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
    
    elif tag in LISTED_ELEMENTS:
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
            data["elementAttrib"]=attribToDict(item.attrib)

        for child in item: 
            tag = modifyTag(child)
            data[tag] = genericSearch( entry, child )

        #print(tag,'f')
    
        return data
    
    
#------------------------------TO MIF GLOBALS-------------------------------------------------------

NAMESPACES_TOMIF = {None:"http://psi.hupo.org/mi/mif","xsi":"http://www.w3.org/2001/XMLSchema-instance"} #Xpath does not support empty namespace key, but when converting back to DOM this is fine.
MIF_NS = NAMESPACES["x"]
MIF = "{%s}" % MIF_NS
       
#----------------------------TO MIF UTILITIES-------------------------------------------------

def isTextElement(text):
        return (isinstance(text,str) or (isinstance(text,dict) and "value" in text.items()))
    
def buildTextElement(name,text): #specifically 
    root = etree.Element(MIF+name)
    if(isinstance(text,dict)):
        for textkey, textval in text.items():
            if(textkey=="value"):
                root.text = textval
            else:
                root.attrib[textkey] = textval   
                    
    elif(isinstance(text,str)):
        root.text=text
        
    return root
                
def parseChildren(root, item): #when recursively parsing through these objects, we have to look at children because their contents may have to be added back to the root
    for subkey, subval in item.items():
        if(subkey=="elementAttrib"):
            for attribkey, attribval in subval.items():
                root.attrib[attribkey] = attribval
            
        elif(isTextElement(subval)):
            root.append(buildTextElement(subkey,subval))
                
        else:
            #print(subkey)
            root.append(genericMifGenerator(subkey,subval))     
    
def genericMifGenerator(rawkey,value): #root is a value in key value pair 
    
    if not MIF in rawkey: #add the namespace
        key = MIF+rawkey
    else:
        key = rawkey
        
    root = etree.Element(key)
    if(isinstance(value,tuple)):
        val = value[1]
    else:
        val = value.copy()
        
    if((rawkey=="experimentList" or rawkey=="interactorList" or rawkey=="availabilityList") and isinstance(val,dict)):

        for expkey, expval in val.items():
            if rawkey=="experimentList":
                childName = "experimentDescription"
            else:
                childName = key[:-4]
            childExp = genericMifGenerator(childName,expval)
            childExp.attrib["id"] = expkey
            root.append(childExp)
    
    elif(rawkey=="participantList"):
        
        for participant in val:
            partElem = etree.Element("participant")
            for partkey, partval in participant.items():
                if(partkey=="participantInteractorList"):
                    for expkey, expval in partval.items():
                        childName = "interactor"
                        childExp = genericMifGenerator(childName,expval)
                        childExp.attrib["id"] = expkey
                        partElem.append(childExp)
                else:
                    partElem.append(genericMifGenerator(partkey,partval))
            root.append(partElem)
            
    elif (rawkey=="attributeList"):
        for item in val:
            root.append(buildTextElement("attribute",item))        
            
    elif(rawkey=="names"): #names is a special case 
        for namekey,nameval in val.items(): 
            if(isinstance(nameval,str)):
                root.append(buildTextElement(namekey,nameval))
            else: #nameval is a list of aliases
                for alias in nameval:
                    root.append(buildTextElement(namekey,alias))
                    
    elif(rawkey=="xref"):
        for xkey, xval in val.items():
            if(xkey=="secRefInd"):
                continue    
            elif(isinstance(xval,dict)): #primaryRef
                root.append(buildTextElement(xkey,xval))
            else: #secondaryRef
                for secref in xval:
                    root.append(buildTextElement(xkey,secref))    
                    
    elif(isinstance(val,dict)):
        parseChildren(root,val)
             
    elif(isinstance(val,list)):
        for item in val:
                
            if key.endswith("List"):
                modifiedKey = key[:-4]
                childElem = etree.Element(modifiedKey)
            else:
                childElem = etree.Element(key)
            root.append(childElem)
            parseChildren(childElem,item)
            
    
    return root      
