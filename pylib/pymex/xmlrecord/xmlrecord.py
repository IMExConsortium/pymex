#utf: # -*- coding-8 -*-
"""
Created on Mon Jun 29 13:56:57 2020
@author: andrei
"""

from lxml import etree as ET
import json
import os

class XmlRecord():
    """XML-based record representation."""

    def modifyTag(self,item,ver):
        """ Modifies tag of an item if necessary."""
        tag = item.tag[self.config[ver]["NSL"]:]
        return tag

    def toNsString(self,ns, prefix=None):
        """Converts namespace to string prefix for element tags."""
        mif_ns = ns[prefix]
        mifstr = "{%s}" % mif_ns
        return mifstr

    def __init__(self, root=None, config=None, post=None):


        if root is not None:
            self.root = root
        else:
            self.root = {}

        self.config = {}
        self.post = post
        #postprocess dictionary structure:
        #{current element : [function call, parent of current element]}
        self.postprocess = {}
        self.recordTree = None
        self.version = None
        if config is not None:

            for ver in config.keys():
                self.config[ver] = {}

                #"loads" in appropriate json file depending on format.
                #config is a deeply nested dictionary:
                #{version: {IN or OUT: {json file as a dictionary} } }
                #config[ver]["IN"] is a json file
                self.config[ver]["IN"] = json.load( open( config[ver]["IN"] ) )
                #what is NSL?
                self.config[ver]["NSL"] = len(self.config[ver]["IN"]["@NS"])+2

                self.config[ver]["OUT"] = json.load( open( config[ver]["OUT"] ) )

                # re-key  default ("*") namespace

                defns = None
                for nk in self.config[ver]["OUT"]["@NS"]:
                    if nk == "*":
                        defns = self.config[ver]["OUT"]["@NS"]["*"]
                if defns is not None:
                    self.config[ver]["OUT"]["@NS"].pop("*", None)
                    self.config[ver]["OUT"]["@NS"][None] = defns

    def parseXml(self, filename, ver, debug=False):

        #dictionary representation of json file
        template = self.config[ver]["IN"]

        #adding version of inputted xml file to metadata
        self.version = ver

        #tree data structure from etree; holds the parsed data from passed in xml file.
        #returns elementTree object
        #documentobject structure
        self.recordTree = ET.parse( filename )
        #find stoichiometry elements if 254:
        print(ver)
        #if (ver == "mif254"):
            #self.findStoich254(recordTree, ver)
        #root object has a tag and attribute
        #root.tag, root.attrib
        #for child in root iterates over children of the root.
        #TODO: test this out with xml file to determine exactly how it works - what constitutes a "child" in the context of these xml files
        rootElem = self.recordTree.getroot()
        #template describes what to expect
        self.genericParse( template, ver, self.root, [] , rootElem, debug )
        return self

    #same as parseXml, but directly takes in an ElementTree objecr rather than converting a file into one.
    def parseXml2(self, ver, debug=False):
        template = self.config[ver]["IN"]

        #adding version of inputted xml file to metadata
        self.version = ver
        rootElem = self.recordTree.getroot()
        self.genericParse( template, ver, self.root, [] , rootElem, debug )
        return self

    def genericParse(self, template, ver, rec, rpath, elem, wrapped=False, debug=False):

        tag = self.modifyTag( elem, ver )

        #find corresponding template
        #else default in json
        #template is the dictionary representation of the appropriate json file, as pulled from the config dictionary
        #ttempl is now just the single row corresponding to appropriate tag
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
                #going two levels up if current element is just a wrapper.
                if  parentElem.getparent() is not None:
                    parentElem = parentElem.getparent()
                else:
                    parentElem = None
        else:
            parentElem = None

        #just recording the parent tag
        if parentElem is not None:
            parentTag = self.modifyTag( parentElem, ver )
            if debug:
                print(" PAR", parentTag )

        else:
            parentTag = None
            if debug:
                print("PAR:  ROOT ELEM !!!")
        #print(parentTag)
        #noting down template for same attributes found under different parents;
        #this is the second level in the json files.
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
        #cwrap is a boolean, says whether current element is a wrapper
        if debug:
            print( "  CWRAP ", cwrap )

        if cwrap:
            #recursing one child deeper if current element is just a wrapper.
            for cchld in elem:
                if debug:
                    print("  CHLD",cchld.tag);

                self.genericParse( template, ver, rec, rpath, cchld, wrapped =True)
                if debug:
                    print( json.dumps(self.root, indent=2) )
            #postprocessing specifications
            #must happen before wrapper check since postprocess elements may be wrappers
            if "postprocess" in ctempl and ctempl["postprocess"] is not None:
                self.post[ctempl["postprocess"]](elem, rec)

            return

        # find current key:
        #checking the attributes, not the tags
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
        # ref is of form /entrySet/entry/experimentList, which is xpath, using actual tags.
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

            #splitting xpath into each tag
            stgt = rtgt.split('/')
            for i in range(1,len(stgt)):
                #checks if each tag is in the rpath that has been passed in this round of recursion.
                if stgt[i] in rpath[i-1]:
                    ##what is supposed to be here??
                    pass
                else:
                    break

            """rewrite as:
            for i in range(len(stgt) - 1):
                if stgt[i] in rpath[i]:
                    pass
                else:
                    break
            """

            #what is the structure and type of rpath?
            #rpath starts as an empty list.
            #this part makes no sense, what i is this?
            #lastmatch is assigned to
            lastmatch = rpath[i-2][stgt[i-1]]
            if cstore == "list":
                if ckey not in rec:
                    rec[ckey] = []
                #appends the information
                rec[ckey].append( lastmatch[stgt[i]][elem.text] )
            elif cstore == "direct":
                rec[ckey] = lastmatch[stgt[i]][elem.text]

        else:
            # build/add current value
            #just assigns cvalue to the text string if not complex
            #if complex, cvalue is a dictionary with the text string udner as value of "value" key
            cvalue = None
            if ccomplex:
                cvalue = {}
                if elem.text:
                    val = str(elem.text).strip()
                    if len(val) > 0:
                        cvalue["value"] = val
            else:
                cvalue = str( elem.text )

            #if ckey in rec:
            #    print(ckey, rec[ckey])

            if cstore  == "direct":
                #rec is a dictionary
                        ##is rec a nested dictionary or is each ckey on the same level?
                        ##can test this and just skip the reference part?
                #ckey is either the tag of the element (first thing after < in xml), or the name as defined in the josn
                #this assigns the actual text of an element to its name.
                #creating new key value pair in rec, key is ckey (tag or name), value is cvalue (text in element)
                rec[ckey] = cvalue
            elif cstore == "list":
                if ckey not in rec:
                    rec[ckey] = []
                    #if list, adds text to the list that is the value of the key (tag or name)
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
                    #ex iattr = id
                    iattr= ikey[1:]
                    #getting the attribute from the xml tree
                    ikeyval = elem.get(iattr)

                    #inside red dictionary, value of ckey (when store is index) is another dictionary, containing
                    #a key (value of attribute in xml) whose value is cvalue (jsut elem.text or dictionary with elem.text)
                    """
                    ex:
                    xml: <primaryRef db="psi-mi" dbAc="MI:0488" id="MI:0465" refType="identity" refTypeAc="MI:0356"/>
                    json:     "availability":{"entry":{"store":"index","ikey":"@id","name":"availabilityList"}}, (pretend these correspond)

                    ikey = "@id"
                    iattr = "id"
                    ikeyval = "MI:0465"
                    rec[availabilityList(from name)][MI:0465] = **cvalue (what is cvalue in this case; no text)


                    """
                    if ikeyval is not None:
                        rec[ckey][ikeyval] = cvalue

            #create xrefInd inside xref
            #what is this? both json do not have index as a key in ctempl
            if "index" in ctempl and ctempl["index"] is not None:
                ckeyRefInd = ctempl["index"]["name"]
                rec[ckey][ckeyRefInd] = {}

            # parse elem contents

            # add dom attributes
            #elem.attrib probably returns a dictionary with the attributes in xml and their values.
            for cattr in elem.attrib:
                #cvalue can be assumed to be dictionary here because it must be complex if contains attributes.
                #in addition to "value": value, adds each attribute and its value to cvalue.
                cvalue[cattr] = str( elem.attrib[cattr] )

            cpath = []
            #seems like rpath is supposed to containg a list of every tag: cvalue pair up to the current element
            #hence, structure is in the order of rpath list
            #here, we append the current tag: cvalue pair to the end and pass it in for recursion.
            for p in rpath:
                cpath.append(p)
            #append wrapper for later reconstruction too?
            cpath.append( {tag: cvalue })

            if 'index' in ctempl:
                iname = ctempl["index"]["name"]
                ientry = ctempl["index"]["entry"]

            #this is important for defining the structure of this rpath
            for cchld in elem:
                cchldTag = self.modifyTag(cchld, ver)
                if debug:
                    print("  CHLD", cchld.tag);
                #passes in cvalue for rec; can assume it is a dictionary since only the last child
                #will be non complex and will skip all instances of treating it like a dictionary
                #
                self.genericParse( template, ver, cvalue, cpath, cchld)

                if 'index' in ctempl:
                    if cchldTag in ientry and ientry[cchldTag] is not None:
                        keyList = ientry[cchldTag]["key"]

                        kval = []
                        for k in keyList:
                            kvl = cchld.xpath(k)
                            if kvl:
                                kval.append(kvl[0])
                        dbkey = ':'.join(kval)
                        rec[ckey][ckeyRefInd][dbkey] = cvalue[cchldTag][0] if type(cvalue[cchldTag]) is list else cvalue[cchldTag]

            if debug:
                print( json.dumps(self.root, indent=2) )

            #postprocessing specifications
            if "postprocess" in ctempl and ctempl["postprocess"] is not None:
                self.post[ctempl["postprocess"]](elem, rec)

        return

    def parseJson(self, file ):
        self.root = json.load( file )
        return self

    def toJson(self):
        return json.dumps(self.root, indent=2)

    #this function would use the postprocessing tag to record data.
    def toXml( self, ver='mif254', rdata = "entrySet", rtype="ExpandedEntrySet" ):
        """Builds Xml elementTree from a Record object."""

        template = self.config[ver]["OUT"]

        #nsmap = self.MIFNS[ver]
        nsmap = template["@NS"]


        return self.mifGenerator( nsmap, ver, template, None,
                                  self.root[rdata], template[rtype] )
        return None

    #ctype is [{"value":"entry", "type":"expandedEntry","name":"entry"}]
    #cdata is root dictionary datastructure
    
    def mifGenerator(self, nsmap, ver, template, dom, cdata, ctype):
        """Returns DOM representation of the MIF record defined by the template.
        """

        self.UID = 1

        name = template["@ROOT"]["name"]
        if "attribute" in template["@ROOT"]:
            attrib = template["@ROOT"]["attribute"]
        else:
            attrib = None

        #dom = ET.Element(self.toNsString(self.MIFNS[ver]) + name,nsmap=nsmap)
        dom = ET.Element(self.toNsString(nsmap) + name,nsmap=nsmap)

        if attrib is not None:
            for a in attrib:

                if ":" in a:
                    (ans,aname)  = a.split(":")
                    qname = self.toNsString(nsmap,prefix=ans) + aname
                else:
                    qname = a

                dom.set(qname,attrib[a])

        for cdef in ctype:
            
            chldLst = self.mifElement( nsmap, ver, template, None, cdata, cdef)
            if chldLst is not None:
                for chld in chldLst:
                    #appending to an ET.element, must be of element type
                    dom.append( chld )

        return dom

    def mifElement(self, nsmap, ver, template, celem, cdata, cdef ):
        """Returns a list of DOM elements (ET.element type ) to be added to 
           the parent and/or decorates parent with attributes and text value .
        """
        retLst = []

        if "wrap" in cdef:
            # add wrapper
            wrapName = cdef["wrap"]
            #creates simple element; no attributes
            wrapElem = ET.Element(self.toNsString(nsmap) + wrapName)
        else:
            wrapElem = None

        if "value" not in cdef: # empty wrapper

            # definition of wrapper contents
            wrappedTypes = template[cdef["type"]]

            empty = True # flag: will skip if nothing inside
            
            #iterating through values in new dictionary, which is just another entry in the json
            for wtDef in wrappedTypes: # go over wrapper content

                if wtDef["value"] in cdata:   # check if data present
                    wElemData = cdata[wtDef["value"]]
                    #iterate through root dictionary, wElemData is a piece of self.root
                    for wed in wElemData: # wrapper contents *must* be a list
                        empty = False # non empty contents

                        if "name" in wtDef:
                            chldName = wtDef["name"]
                            #print("90909")
                            #print(chldName)
                        else:
                            chldName = wtDef["value"]

                        # create content element inside a wrapper
                        # tag of new element is an explicitly defined name in root,
                        # or just the same name as the value.
                        
                        chldElem = ET.Element(self.toNsString(nsmap) + chldName)
                        wrapElem.append(chldElem)

                        # fill in according to element definition
                        for wtp in template[wtDef["type"]]:
                            wclLst = self.mifElement( nsmap, ver, template,
                                                      chldElem, wed, wtp)
                            # add contents
                            if wclLst is not None:
                                for wcd in wclLst:
                                    chldElem.append(wcd)

            if not empty:

                return [wrapElem]

            else:
                return None

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
                    chldElem = ET.Element(self.toNsString(nsmap) + elemName)
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

            chldElem = ET.Element(self.toNsString(nsmap) + elemName)

            if cdef["type"]=='$TEXT': # text child element
                chldElem = ET.Element(self.toNsString(nsmap) + elemName)
                chldElem.text = str( celemData )
                retLst.append(chldElem)
            else: # complex content: build recursively
                contType = template[cdef["type"]]

                for contDef in contType: # go over definitions
                    cldLst = self.mifElement( nsmap, ver, template,
                                              chldElem,
                                              celemData,
                                              contDef)
                    if cldLst is not None:
                        for cld in cldLst:
                            chldElem.append( cld )
                    else:
                        cldLst = None

                if wrapElem is not None:       # if present, add to wrapper
                    if chldElem is not None:
                        wrapElem.append( chldElem )
                    else:
                       wrapElem = None
                elif chldElem is not None:     #  otherwise add to return list
                    retLst.append( chldElem )

        if "postprocess" in cdef:
            function = self.post[cdef["postprocess"]](cdata, celem, wrapElem)

        if wrapElem is not None and len(wrapElem) > 0:
            if debug:
                print( "wrapElem:", ET.tostring(wrapElem, pretty_print=True).decode("utf-8") )
            return [wrapElem]
        else:
            if debug:
                print( "retLst:", retLst )
        
        return retLst
