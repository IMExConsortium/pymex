#-------------------------------- GLOBALS -------------------------------------------------------------

MIF_NS = "http://psi.hupo.org/mi/mif"
MIF = "{%s}" % MIF_NS
NSMAP = {None : MIF_NS}

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

