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

    def __init__(self, root=None, config=None):

        if root is not None:
            self.root = root
        else:
            self.root = {}

        self.config = {}
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
                
    def parseXml(self, filename, ver, debug=False):
        
        template = self.config[ver]["IN"]
        
        recordTree = ET.parse( filename )
        rootElem = recordTree.getroot()
        
        self.genericParse( template, ver, self.root, [] , rootElem, debug )
        return self

    def genericParse(self, template, ver, rec, rpath, elem, wrapped=False, debug=False):
      
        tag = self.modifyTag( elem, ver )

        #find corresponding template
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
        #print(parentTag)
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
        if debug:
            print( "  CWRAP ", cwrap )

        if cwrap:
            for cchld in elem:
                if debug:
                    print("  CHLD",cchld.tag);

                self.genericParse( template, ver, rec, rpath, cchld, wrapped =True)
                if debug:
                    print( json.dumps(self.root, indent=2) )                
            return 
        
        # find current key:        
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

            stgt = rtgt.split('/')
            for i in range(1,len(stgt)):
                if stgt[i] in rpath[i-1]:
                    pass
                else:
                    break

            lastmatch = rpath[i-2][stgt[i-1]]
            if cstore == "list":
                if ckey not in rec:
                    rec[ckey] = []
                rec[ckey].append( lastmatch[stgt[i]][elem.text] )
            elif cstore == "direct":
                rec[ckey] = lastmatch[stgt[i]][elem.text]
                
        else:
            # build/add current value
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
                        rec[ckey][ikeyval] = cvalue        
            
            #create xrefInd inside xref
            if "index" in ctempl and ctempl["index"] is not None:
                ckeyRefInd = ctempl["index"]["name"]
                rec[ckey][ckeyRefInd] = {}
                
            # parse elem contents
                
            # add dom attributes
            for cattr in elem.attrib:
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
                    

            if debug:
                print( json.dumps(self.root, indent=2) )
        return
        
    def parseJson(self, file ):
        self.root = json.load( file )
        return self

    def toJson(self):
        return json.dumps(self.root, indent=2)

    def toXml( self, ver='mif254', rdata = "entrySet", rtype="ExpandedEntrySet" ):
        """Builds Xml elementTree from a Record object."""

        template = self.config[ver]["OUT"]
        
        #nsmap = self.MIFNS[ver]
        nsmap = template["@NS"]

        return self.mifGenerator( nsmap, ver, template, None,
                                  self.root[rdata], template[rtype] )
        return None
    
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
                    dom.append( chld )
            
        return dom
    
    def mifElement(self, nsmap, ver, template, celem, cdata, cdef ):
        """Returns a list of DOM elements to be added to the parent and/or decorates  
           parent with attributes and text value . 
        """
        retLst = []
        if "wrap" in cdef:
            # add wrapper            
            wrapName = cdef["wrap"]
            wrapElem = ET.Element(self.toNsString(nsmap) + wrapName)        
        else:
            wrapElem = None
            
        if "value" not in cdef: # empty wrapper        
            # wrapper contents definition
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

                        # create content element inside a wrapper
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

        if wrapElem is not None and len(elemData) > 0:            
            return [wrapElem]
        
        return retLst    
    
