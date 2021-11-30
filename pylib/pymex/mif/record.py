# -*- coding: utf-8 -*-
"""
Created on Wed Aug 19 02:05:33 2020

@author: andrei
"""

import os
import pymex
from lxml import etree as ET
from pymex import xmlrecord, mif

class Record(xmlrecord.XmlRecord):
    """MIF record representation. Inherits XML parsing and serialization from xml.XmlRecord"""

    def __init__(self, root=None):

        myDir = os.path.dirname( os.path.realpath(__file__))
        self.mifConfig = { "mif254": {"IN": os.path.join( myDir, "defParse254.json"),
                                      "OUT": os.path.join( myDir, "defMif254.json" )},
                           "mif300": {"IN": os.path.join( myDir, "defParse300.json"),
                                      "OUT": os.path.join( myDir, "defMif300.json" )}}
        
        super().__init__( root,
                          config = self.mifConfig,
                          postproc = { "stoich254":self._stoich254,
                                       "stoich254w":self._stoich254w,
                                       "addstoich254":self._addstoich254} )
                
    def parseMif(self, filename, ver="mif254", debug=False):
        return self.parseXml( filename, ver=ver )

    def toMif( self, ver='mif254' ):
        """Builds MIF elementTree from a Record object."""
        
        #self._stoichiometryConvert( ver )        
        
        return self.toXml( ver, "entrySet", "ExpandedEntrySet" )
        
    def _stoich254( self, elem=None, rec=None, cval=None ):

        #print("ELEM", elem)
        #print("REC", rec["participant"].keys())
        #print("CCH(pre): ", cval.keys())

        
        if 'attribute' in cval.keys():
            datt = None
            for attr in cval['attribute']:
                if attr['name'] == "comment":
                    cav = attr['value'].strip().lower()
                    if cav.startswith("stoichiometry:"):
                        print("_stoich254: ", attr )
                        cav = cav.replace("stoichiometry:","").strip()
                        cval['stoichiometry']=cav
                        datt = attr
            if datt is not None:
                cval['attribute'].remove(datt)
                
        print("CCH(post): ", cval.keys())
        
    def _stoich254w( self, arg1=None, arg2=None, arg3=None ):
        print("_stoich254w: NOOP")

    def _addstoich254( self, cdata=None, celem=None, cwrap=None, debug=False ):
        if debug:
            print("_addstoich254: BEGIN")
            print("cdata -> ", cdata.keys())
            print("celem -> ", celem)
            print("cwrap -> ", cwrap)

        if "stoichiometry" in cdata.keys():
            if debug:
                print("adding stoichiometry: ", cdata["stoichiometry"])
                # <attribute name="comment">stoichiometry: #val</attriute>
            chldElem = ET.Element( "attribute")
            chldElem.text = "stoichiometry: " + str( cdata["stoichiometry"] )
            chldElem.set("name","comment")
            cwrap.append(chldElem)
        if debug:
            print("_addstoich254: DONE")
        
    @property
    def entry(self):
        """Returns the first (default) entry of the record"""
        return pymex.Entry( self.root['entrySet']['entry'][0] )

    @property
    def entryCount(self):
        return len( self.root['entrySet']['entry'])

    def getEntry( self, n = 0 ):
        "Returns i-th entry of the record."""
        if n < len( self.root['entrySet']['entry'] ):
            return mif.Entry( self.root['entrySet']['entry'][n] )
        else:
            return None

    @property
    def interactions(self):
        """Returns interactions of the first (default) entry of the record."""
        return mif.Entry( self.root['entrySet']['entry'][0] ).interactions

    @property
    def interactionCount(self):
        return len( self.root['entrySet']['entry'][0]["interaction"])

    def getInteraction( self, n ):
        return pymex.Interaction( self.root['entrySet']['entry'][0], n )


class Entry():
    """MIF Entry representation."""
    def __init__( self, entry ):
        self._entry = entry

    @property
    def interactions( self ):
        ret = []
        for i in range( 0, len( self._entry["interaction" ]) ):
            ret.append( mif.Interaction( self._entry, n=i ) )
        return ret

    @property
    def interactionCount( self ):
        return len( self._entry[ "interaction" ] )

    def getInteraction( self, n ):
        return mif.Interaction( self._entry , n )

    @property
    def abstIinteractions( self ):
        ret = []
        for i in range( 0, len( self._entry["abstInteraction" ]) ):
            ret.append( mif.AbstInteraction( self._entry, n=i ) )
        return ret

    @property
    def abstInteractionCount( self ):
        return len( self._entry[ "abstInteraction" ] )

    def getAbstInteraction( self, n ):
        return mif.AbstInteraction( self._entry , n )


    @property
    def source(self):
        return mif.Source(self._entry["source"])
