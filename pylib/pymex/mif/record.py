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

        postFuncs = {"stoichiometry":self.isSpecial, "getStoich":self.buildStoich}
        #initializes this class to have all the properties of the parent class
        super().__init__(root, config=self.mifConfig, post=postFuncs )

    def parseMif(self, filename, ver="mif254", debug=False):
        return self.parseXml( filename, ver=ver )

    def toMif( self, ver='mif254' ):
        """Builds MIF elementTree from a Record object."""

        dom = self.toXml( ver, "entrySet", "ExpandedEntrySet" )        

        return dom

    def buildStoich(self, data, element, wrapElem):
        #if wrap elem is not None, append new stoichiometry attribute to it.
        #using info in cdata["stoichiometry"] (a)
        #use mifElememt to build the new element using attribute definition
        #return generated dom.
        if wrapElem is not None:
            if "stoichiometry" in data:
                stoich = data["stoichiometry"]
                value = stoich["value"]
                newString = "Stoichiometry: " + value
                newAttr = ET.SubElement(wrapElem, "attribute", {"name": "comment"})
                newAttr.text = newString
        return

    def isSpecial(self, element, rec):
        """Checks if post process element is an attribute list element 
           containing a stoichiometry attribute, converts dictionary format if so
        """
        stoichAttribute = self.getStoichiometry(element, rec)
        if stoichAttribute is not None:
            newRec = self.stoich254to300(stoichAttribute)

            rec["stoichiometry"] = {'value': newRec}

            return True
        return False

    def getStoichiometry(self, elem, rec):
        """Checks if rec contains an attribute which contains the text Stoichiometry"""
        attributes = rec["attribute"]
        for element in attributes:
            if "value" in element:
                value = element["value"]
                if value.strip().lower().startswith("stoichiometry"):
                    rec["attribute"].remove(element)
                    return value

        return None

    def stoich254to300(self,stoich):
        """Uses stoichiometry attribute text to extract the stoichiometry value"""
        value = ""
        #parsing text for stoichiometry value
        for char in stoich:
            if char.isnumeric() or char==".":
                value = value + char

        return value

    @property
    def entry(self):
        """Returns the first (default) entry of the record"""
        return mif.Entry( self.root['entrySet']['entry'][0] )

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
        return mif.Interaction( self.root['entrySet']['entry'][0], n )


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
