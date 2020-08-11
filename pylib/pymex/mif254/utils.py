from lxml import etree


#-------------------------------- GLOBALS -------------------------------------------------------------
MIF_NS = "http://psi.hupo.org/mi/mif"
MIF = "{%s}" % MIF_NS
NSMAP = {None : MIF_NS}
NAMESPACES_TOMIF = {None : MIF_NS}

NAMESPACES = {"x":MIF_NS}
LEN_NAMESPACE = len(NAMESPACES["x"])+2 #because of the two brackets around the text
IDENTIFIED_LISTED_ELEMENTS = ["interactor","experimentDescription","participant","interaction"] #these need to be hashed by ID in the recursive case
LISTED_ELEMENTS = ["hostOrganismList","experimentalRoleList","experimentalPreparationList","featureList","featureRangeList"]

#-------------------------------- UTILITIES --------------------------------------------------

def modifyTag(item): 
    """ Modifies tag of an item if necessary."""
    tag = item.tag[LEN_NAMESPACE:]
    if not tag in IDENTIFIED_LISTED_ELEMENTS:
        return tag
    elif tag in LISTED_ELEMENTS: #Get rid of "list", as per Salwinski's preferences
        tag = tag[:-4]
    else:
        if tag=="hostOrganism": 
            tag+= " ncbiTaxId:" + item.attrib.get("ncbiTaxId")
        else:
            tag+= " id:" + item.attrib.get("id")
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




#----------------------------TO MIF UTILITIES-------------------------------------------------

def isTextElement(text):
        return (isinstance(text,str) or (isinstance(text,dict) and "value" in text.items()))
    
def buildTextElement(name,text): #specifically

    if name.startswith('_'):
        return None
    root = etree.Element(MIF+name)
    print("btext", name, type(text),text)
    if(isinstance(text,dict)):
        for textkey, textval in text.items():
            print(textkey, textval)
            if(textkey=="value"):
                root.text = textval
            else:
                root.attrib[textkey] = textval   
                    
    elif(isinstance(text,str)):
        root.text=text
        
    return root
                
def parseChildren(root, item):
    #when recursively parsing through these objects,
    #we have to look at children because their contents
    #may have to be added back to the root
    print( type(item), item )
         
    for subkey, subval in item.items():

        print("parseChildren: subkey, subval", subkey, type(subval))
        if(subkey=="elementAttrib"):
            for attribkey, attribval in subval.items():
                root.attrib[attribkey] = attribval
            
        elif( isTextElement(subval) ):
            elem = buildTextElement(subkey,subval)
            if elem is not None:
                root.append( buildTextElement(subkey,subval) )
                
        else:
            #print(subkey)
            elem = genericMifGenerator(subkey,subval)
            if elem is not None:
                root.append( elem )     
   
def genericMifGenerator( rawkey, value ):
    #root is a value in key value pair 

    if rawkey.startswith("_"):
        return None
    
    if not MIF in rawkey: #add the namespace
        key = MIF+rawkey
    else:
        key = rawkey
        
    print("key",key)
    
    root = etree.Element(key)
    if(isinstance(value,tuple)):
        val = value[1]
    else:
        val = value.copy()
        
    if( (rawkey=="experimentList" or rawkey=="interactorList" or
         rawkey=="availabilityList") and isinstance(val,dict)):

        for expkey, expval in val.items():
            if rawkey=="experimentList":
                childName = "experimentDescription"
            else:
                childName = key[:-4]            
            childExp = genericMifGenerator(childName,expval)
            if childExp is not None:
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
                        if childExp is not None:
                            childExp.attrib["id"] = expkey
                            partElem.append(childExp)
                else:
                    elem = genericMifGenerator(partkey,partval)
                    if elem is not None:
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
            if(xkey=="secRefInd" or xkey.startswith('_') ):
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

