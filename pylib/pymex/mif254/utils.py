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
   
