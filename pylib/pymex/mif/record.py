# -*- coding: utf-8 -*-
"""
Created on Mon Jun 29 13:56:57 2020
@author: andrei
"""

from lxml import etree as ET
import json
from xml.dom import minidom
import os

from pymex import mif

class Record(mif.XmlRecord):
    """MIF record representation."""
    
    def modifyTag(self,item,ver): 
        """ Modifies tag of an item if necessary."""
        tag = item.tag[self.LEN_NAMESPACE[ver]:]
        return tag
    
    def toNsString(self,ns): 
        """Converts namespace to string prefix for element tags."""
        mif_ns = ns[None]
        mifstr = "{%s}" % mif_ns
        return mifstr

    def __init__(self, root=None):

        if root is not None:
            self.root = root
        else:
            self.root = {}
        
        self.NAMESPACES = { "mif254":"http://psi.hupo.org/mi/mif",
                            "mif300":"http://psi.hupo.org/mi/mif300"}
        self.LEN_NAMESPACE = {"mif254":28, "mif300":31}
        self.MIFNS = { "mif254":{None:"http://psi.hupo.org/mi/mif",
                                 "xsi":"http://www.w3.org/2001/XMLSchema-instance"},
                       "mif300":{None:"http://psi.hupo.org/mi/mif300",
                                 "xsi":"http://www.w3.org/2001/XMLSchema-instance"}}
        
        self.PARSEDEF={"mif254":"defParse254.json",
                       "mif300":"defParse300.json"}
        self.MIFDEF= {"mif254":"defMif254.json",
                      "mif300":"defMif300.json"}
        
    @property
    def entry(self):
        return self.getEntry()
    
    def getEntry(self, id = 0):
        if len(self.root) > id:
            return Entry(self.root, id)
        else:
            return None
    
    @property          
    def interaction(self):
        
        ret = []
        
        for i in Entry( self.root ).interaction:
            ret.append( self.getEntry().getInteraction(id) )
        
        #return Entry(self.root).interaction
        return ret
        
    def __getitem__(self, id):
        return self.getEntry().getInteraction(id)

    def parseMif(self, filename, ver="mif254", debug=False):
        
        json_dir = os.path.dirname( os.path.realpath(__file__) )

        template = json.load( open( os.path.join(json_dir, self.PARSEDEF[ver]) ) )
        
        recordTree = ET.parse( filename )
        rootElem = recordTree.getroot()
        
        self.genericParse( template, ver, self.root, [] , rootElem, debug )
        return self


    def toMif( self, ver='mif254' ):
        """Builds MIF elementTree from a Record object."""

        json_dir = os.path.dirname( os.path.realpath(__file__) )
        template = json.load( open( os.path.join(json_dir, self.MIFDEF[ver]) ) )
            
        nsmap = self.MIFNS[ver]

        return self.mifGenerator(nsmap, ver, template, None, self.root["entrySet"],
                                               template['ExpandedEntrySet'] )
        return None
    
    
