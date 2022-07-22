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

    def modifyTag( self, item, ver ):
        """ Modifies tag of an item if necessary."""

        if self.config[ver]["NSL"] >2:
            return item.tag[self.config[ver]["NSL"]:]
        else:
            return item.tag[:]

    def toNsString( self, ns, prefix=None ):
        """Converts namespace to string prefix for element tags."""
        
        mif_ns = ns[prefix]
        mifstr = "{%s}" % mif_ns
        print(prefix,ns[prefix], mifstr)
        return mifstr

    def __init__(self, root=None, config=None, preproc=None, postproc=None):

        self.fversion = None 
        
        if root is None:
            self.root = {}
        else:
            self.root = root

        if preproc is None:            
            self.preproc = {}
        else:
            self.preproc = preproc

        if postproc is None:            
            self.postproc = {}
        else:
            self.postproc = postproc
                        
        self.config = {}
            
        self.recordTree = None
        
        if config is not None:

            for ver in config.keys():
                self.config[ver] = {}

                self.config[ver]["IN"] = json.load( open( config[ver]["IN"] ) )
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


    def parseXmlTree(self, xmltree, ver, debug=False):
        template = self.config[ver]["IN"]
        self.fversion = ver
        self.recordTree = xmltree
        
        if debug:
            print(ver)
        
        rootElem = self.recordTree  #.getroot()        
        self.genericParse( template, ver, self.root, [], rootElem, debug )
        
        print(json.dumps(self.root, indent=2))
        return self

    def parseXmlStr(self, xmlstr, ver, debug=False):
        template = self.config[ver]["IN"]
        self.fversion = ver

        try:
            self.recordTree = ET.fromstring( xmlstr )
            #lxml.etree.XMLSyntaxError
        except ET.XMLSyntaxError:
            return None

        if debug:
            print(ver)

        print("XMLREC:", ET.tostring( self.recordTree, pretty_print=True).decode() )
    
        print(self.recordTree)
        rootElem = self.recordTree  #.getroot()        
        self.genericParse( template, ver, self.root, [], rootElem, debug )
        
        print(json.dumps(self.root, indent=2))
        return self

    def parseXml(self, filename, ver, debug=False):
        template = self.config[ver]["IN"]
        self.fversion = ver

        try:
            self.recordTree = ET.parse( filename )
            #lxml.etree.XMLSyntaxError
        except ET.XMLSyntaxError:
            return None

        if debug:
            print(ver)
            
        rootElem = self.recordTree.getroot()        
        self.genericParse( template, ver, self.root, [], rootElem, debug )
        return self

    # same as parseXml, but directly takes in an ElementTree objecr
    # rather than converting a file into one.
    
    def parseXml2(self, ver, debug=False):
        template = self.config[ver]["IN"]
        self.fversion = ver
        
        rootElem = self.recordTree.getroot()
        self.genericParse( template, ver, self.root, [], rootElem, debug )
        return self

    def genericParse( self, template, ver, rec, rpath, elem,
                      wrapped=False, dropped=False, debug=False):

        tag = self.modifyTag( elem, ver )

        if tag in template:
            ttempl = template[tag]
        else:
            ttempl = template["*"]

        if  debug:
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
            parentTag = self.modifyTag( parentElem, ver )
            if debug:
                print(" PAR", parentTag )

        else:
            parentTag = None
            if debug:
                print("PAR:  ROOT ELEM !!!")

        ctempl = None
                
        if parentTag is not None and parentTag in ttempl:
            ctempl = ttempl[parentTag]

        if ctempl is None and wrapped:
            wrParentElem = elem.getparent()
            wrParentTag = None
            if wrParentElem is not None:
                wrParentTag = self.modifyTag( wrParentElem, ver )

            if wrParentTag is not None and wrParentTag in ttempl:
                ctempl = ttempl[wrParentTag]

        if ctempl is None:
            ctempl = ttempl["*"]
            
        if debug:
            print("  CTEMPL", ctempl )

        
        if "drop" in ctempl and ctempl["drop"] is not None: 
            cdrop = ctempl["drop"]
        else:
            if  "drop" in template["*"]["*"]:
                cdrop = template["*"]["*"]["drop"]
            else:
                cdrop = False

        
        
        if "wrapper" in ctempl and ctempl["wrapper"] is not None:
            cwrap = ctempl["wrapper"]
        else:
            cwrap = template["*"]["*"]["wrapper"]

        if debug:
            print( "  CWRAP ", cwrap )

        if( "preproc" in ctempl ):
            if debug:
                print("\nPREP:", ctempl["preproc"], self.preproc[ ctempl["preproc"] ])
                print( tag, elem, list(rec.keys() ), sep=" || " )
            self.preproc[ ctempl["preproc"] ]()

        if cdrop:
            return
            
        if cwrap:
            for cchld in elem:
                if debug:
                    print("  CHLD",cchld.tag);

                self.genericParse( template, ver, rec, rpath, cchld, wrapped=True)
                if debug:
                    print( json.dumps(self.root, indent=2) )

            if( "postproc" in ctempl ):
                if debug:
                    print("\nWRAPPED:", ctempl["post"],
                          self.postproc[ ctempl["postproc"] ] )                    
                    print(tag, elem, list( rec.keys() ) ,sep=" || ")
                self.postproc[ ctempl["postproc"] ](elem, rec, rpath)

            return 
    
        if "name" in ctempl and ctempl["name"] is not None:
            ckey = ctempl["name"]
        else:
            ckey = tag

        if "complex" in ctempl and ctempl["complex"] is not None:
            ccomplex = ctempl["complex"]
        else:        
            ccomplex = template["*"]["*"]["complex"]

        rtgt  = None
        if "reference" in ctempl and ctempl["reference"] is not None:
             rtgt = ctempl["reference"]
        else:    
            rtgt = template["*"]["*"]["reference"]
            
        if "store" in ctempl and ctempl["store"] is not None:
            cstore = ctempl["store"]
        else:
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
            lastmatch = rpath[i-2][stgt[i-1]]
            if cstore == "list":
                #print("rec:", list(rec.keys()),"last",list(lastmatch.keys()),"ckey:", ckey,"stgt:",stgt[i],elem.text)
                if ckey not in rec:
                    rec[ckey] = []
                    #print("!!!")
                    
                ####  missing referenced value - create a placeholder
                if stgt[i] not in lastmatch:
                    lastmatch[stgt[i]]={}
                if elem.text not in lastmatch[stgt[i]]:
                    lastmatch[stgt[i]][elem.text] = {}
                #####

                
                rec[ckey].append( lastmatch[stgt[i]][elem.text] )
            elif cstore == "direct":
                rec[ckey] = lastmatch[stgt[i]][elem.text]

        else:
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
                        if  ikeyval not in rec[ckey]:
                            # new index value
                            rec[ckey][ikeyval] = cvalue   
                        else:
                            # referred to (but empty) value
                            cvalue = rec[ckey][ikeyval]   
                                                                                                            
            if "index" in ctempl and ctempl["index"] is not None:
                ckeyRefInd = ctempl["index"]["name"]
                rec[ckey][ckeyRefInd] = {}
            
            for cattr in elem.attrib:                
                if isinstance(cvalue, dict):
                    cvalue[cattr] = str( elem.attrib[cattr] )

            cpath = []
            for p in rpath:
                cpath.append(p)

            cpath.append( {tag: cvalue })

            if 'index' in ctempl:
                iname = ctempl["index"]["name"]
                ientry = ctempl["index"]["entry"]

            for cchld in elem:
                cchldTag = self.modifyTag(cchld, ver)
                if debug:
                    print("  CHLD", cchld.tag);
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

            if "atrname" in ctempl:                
                #print(ctempl["atrname"],ctempl["atrpath"] )  #,cvalue[ctempl["atrname"]])
                pass
                
            if "postproc" in ctempl:
                if debug:
                    print( "\nUNWRAPPED:", ctempl["post"], self.postproc[ ctempl["postproc"] ] )
                    print(tag, elem, list(rec.keys()) ,sep = " || ")
                self.postproc[ ctempl["postproc"] ](elem, rec, cvalue)
            if debug:
                print( json.dumps(self.root, indent=2) )
                                       
        return

    def parseJson(self, file ):
        self.root = json.load( file )
        return self

    def toJson(self):
        return json.dumps(self.root, indent=2)

    def toXml( self, ver='mif254', rdata = "entrySet", rtype="ExpandedEntrySet",
               debug=False ):
        """Builds Xml elementTree from a Record object."""

        template = self.config[ver]["OUT"]

        nsmap = template["@NS"]


        return self.mifGenerator( nsmap, ver, template, None,
                                  self.root[rdata], template[rtype], debug )
        return None

    #ctype is [{"value":"entry", "type":"expandedEntry","name":"entry"}]
    #cdata is root dictionary datastructure
    
    def mifGenerator(self, nsmap, ver, template, dom, cdata, ctype, debug=False):
        """Returns DOM representation of the MIF record defined by the template.
        """

        self.UID = 1

        name = template["@ROOT"]["name"]
        if "attribute" in template["@ROOT"]:
            attrib = template["@ROOT"]["attribute"]
        else:
            attrib = None

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
            
            chldLst = self.mifElement( nsmap, ver, template, None, cdata, cdef, debug)
            if chldLst is not None:
                for chld in chldLst:
                    #appending to an ET.element, must be of element type
                    dom.append( chld )

        return dom

    def mifElement(self, nsmap, ver, template, celem, cdata, cdef, debug=False):
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

            wrappedTypes = template[cdef["type"]]

            empty = True # flag: will skip if nothing inside
            
            for wtDef in wrappedTypes: # go over wrapper content

                if wtDef["value"] in cdata:   # check if data present
                    wElemData = cdata[wtDef["value"]]
                    
                    for wed in wElemData: # wrapper contents *must* be a list
                        empty = False # non empty contents

                        if "name" in wtDef:
                            chldName = wtDef["name"]                            
                        else:
                            chldName = wtDef["value"]
                        
                        chldElem = ET.Element(self.toNsString(nsmap) + chldName)
                        wrapElem.append(chldElem)

                        for wtp in template[wtDef["type"]]:
                            wclLst = self.mifElement( nsmap, ver, template,
                                                      chldElem, wed, wtp)
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
            elemData = [ elemData ]

        for celemData in elemData: 
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

        if "postproc" in cdef:
            function = self.postproc[cdef["postproc"]](cdata, celem, wrapElem)

        if wrapElem is not None and len(wrapElem) > 0:
            if debug:
                print( "wrapElem:", ET.tostring(wrapElem, pretty_print=True).decode("utf-8") )
            return [wrapElem]
        if debug:
            print( "retLst:", retLst )
        return retLst
