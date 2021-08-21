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

        #initializes this class to have all the properties of the parent class
        super().__init__(root, config=self.mifConfig )

    def parseMif(self, filename, ver="mif254", debug=False):
        return self.parseXml( filename, ver=ver )



    def toMif( self, ver='mif254' ):
        """Builds MIF elementTree from a Record object."""


        #goal is to eliminate this line.
        #tested: it doesn't even work - returns an error with test case.
        #self._stoichiometryConvert( ver )

        dom = self.toXml( ver, "entrySet", "ExpandedEntrySet" )

        # print(ET.tostring(dom, pretty_print=True))
        # if (self.version=="mif254"):
        #     print("mif254")
        #     self.findStoich254(dom, ver)
        # elif (self.version=="mif300"):
        #     self.findStoich300(dom, ver)
        # print("this is preprocess")
        # print(self.postprocess)
        #
        # if (not ver==self.version):
        #     print("entered conversion")
        #     for stoich in self.postprocess:
        #         if ver == "mif254":
        #             self.stoich300to254(stoich, self.postprocess[stoich])
        #         elif ver == "mif300":
        #             self.stoich254to300(stoich, self.postprocess[stoich])

#===========================#


        if (not ver==self.version):
            print("conversion")
            print(self.postprocess)
            #evaluating post process functions, which are the keys of the self.postprocess dictionary
            for x in self.postprocess:

                print(x)
                parentElem = self.postprocess[x][1]
                elem = x
                eval(self.postprocess[x][0])

        print("testing to se")
        print("length of self.postprocess: " + str(len(self.postprocess)))

        return dom

    # def test(self, num):
    #     print("this is the final")
    #     self.testvariable = num + self.testvariable
    #     return





    #ver is version we are converting to
    def stoichconvert(self, elementTree, ver, participant, stoich):
        if (Record.isStoichiometry(self, stoich, self.version)):
            newParticipant = Record.findParticipant(self, participant, elementTree, ver)
            if (newParticipant is not None):
                print("replacing new Participant")
                if (ver=="mif254"):
                    Record.stoich300to254(self, newParticipant, stoich)
                elif (ver=="mif300"):
                    print("converting to 300")
                    Record.stoich254to300(self, newParticipant, stoich)
                print("does this even work??????")
            else:
                print("will not convert; no valid participants")
        else:
            print("non stoich found")
        return

    #ver is version of self (current Record object)
    #invariant: if self.version is 300, elem must be a stoichiometry element since it only takes stoich elements at parsing
    def isStoichiometry(self, elem, ver):
        if (ver == 'mif300'):
            return True
        elif (ver == 'mif254'):
            for x in elem.iter():
                if (x.tag[self.config[ver]["NSL"]:] == "attribute" and "name" in x.attrib):
                    if (x.attrib["name"]=="comment" and "Stoichiometry" in x.text):
                        return True
        else:
            return False

    def findParticipant(self, participant, elementTree, ver):
        #getting participant id from old participant
        attributes = participant.attrib
        id = attributes.get("id")
        print("participant ID: " + str(id))
        #parsing new elementTree for matching participants
        allElems = elementTree.findall(".//")
        for elem in allElems:
            #print(elem.tag[self.config[self.version]["NSL"]:])

            if elem.tag[self.config[ver]["NSL"]:]=="participant" and elem.attrib["id"]==id:
                return elem

        return None





    # #fucntion for finding all stoich elements in the reconstructed mif tree
    # def findStoich254(self, elementTree, ver):
    #     for x in elementTree.iter():
    #         if (x.tag[self.config[ver]["NSL"]:] == "attribute" and "name" in x.attrib):
    #             if (x.attrib["name"]=="comment" and "Stoichiometry" in x.text):
    #                 #appending all 254 stoichiometry elements to postprocess list
    #                 print("this must work")
    #                 self.postprocess[x.getparent().getparent()] = x.getparent()
    #                 print(self.postprocess)
    #
    # def findStoich300(self, elementTree, ver):
    #     print("at least here")
    #
    #     for x in elementTree.iter():
    #
    #         if (x.tag[self.config[ver]["NSL"]:] == "stoichiometry"):
    #             print("found stoich")
    #             #appending all 300 stoichiometry elements to postprocess list
    #             self.postprocess[x.getparent()] = x

    #function for creating and adding 254 version of stoichiometry data using 300 version element:
    def stoich300to254(self, participant, stoich):
        #stoichiometry value
        # print("debug 5")
        # print(stoich)
        value = stoich.attrib["value"]
        #print(value)

        #adding data in 254 format:

        #first creating attribute list wrapper
        attrList = ET.SubElement(participant, "attributeList")
        #creating the attribute element that holds the Stoichiometry data
        stoichElem = ET.SubElement(attrList, "attribute", {"name": "comment"})
        #creating string for attribute text:
        stoichText = "Stoichiometry: " + str(value)
        stoichElem.text = stoichText

        return

    #function for creating and adding 300 version of stoichiometry data using 254 version element:
    def stoich254to300(self, participant, stoich):
        oldStoich = participant[-1]
        participant.remove(oldStoich)
        #participant[-1].clear()
        #stoichiometry value
        value = ""
        #parsing text for stoichiometry value
        text = stoich[0].text
        for char in text:
            if char.isnumeric() or char==".":
                value = value + char


        ET.SubElement(participant, "stoichiometry", {"value": value})
        return

    # #how does this currently handle it?
    # def _stoichiometryConvert(self, ver):
    #
    #     print("stoichiometry conversion")
    #
    #     for e in self.root["entrySet"]["entry"]:
    #         for i in e["interaction"]:
    #             for p in i["participant"]:
    #                 if ver == 'mif254':
    #                     # find mif300 stoichiometry
    #                     stset = False
    #                     if "stoichiometry" in p:
    #                         stval = str( p["stoichiometry"]["value"] )
    #                         stset =True
    #                     else:
    #                         stval = None
    #
    #                     if "stoichiometryRange" in p:
    #                         stmin = str( p["stoichiometryRange"]["minValue"] )
    #                         stmax = str( p["stoichiometryRange"]["maxValue"] )
    #                         stset =True
    #                     else:
    #                         stmin = None
    #                         stmax = None
    #
    #                     if stset:
    #                         # replace/add mif254 stoichiometry
    #                         if "attribute" not in p:
    #                             p["attribute"]={}
    #                         ast = None
    #                         for a in p["attribute"]:
    #                             if ("value" in a and
    #                                 a["value"].startswith("Stoichiometry:") ):
    #                                 ast = a
    #                         if ast is None:
    #                             ast =  {'name': 'comment', 'nameAc': 'MI:0612'}
    #                             p["attribute"].append(ast)
    #
    #                         if stval is not None:
    #                             ast["value"] = "Stoichiometry: " + stval
    #
    #                         elif stmin is not None and stmax is not None:
    #                             strng = stmin + " : " + stmax
    #                             ast["value"] = "StoichiometryRange: " + strng
    #
    #                 elif ver == 'mif300':
    #
    #                     # find mif254 stoichiometry
    #                     stval = None
    #                     stmin = None
    #                     stmax = None
    #                     if "attribute" in p:
    #                         for a in p["attribute"]:
    #                             if ("value" in a and
    #                                 a["value"].startswith("Stoichiometry:")
    #                                 ):
    #                                     vcol= a["value"].split(" ")
    #                                     stval = vcol[1]
    #                                     p["attribute"].remove( a )
    #                                     break
    #
    #                             if ("value" in a and
    #                                 a["value"].startswith("StoichiometryRange:")
    #                                 ):
    #                                     vcol= a["value"].split(" ")
    #                                     stmin = vcol[1]
    #                                     stmax = vcol[3]
    #                                     p["attribute"].remove( a )
    #                                     break
    #
    #                     # replace/add mif300 stoichiometry
    #                     if stval is not None:
    #                         st = p.setdefault("stoichiometry",{})
    #                         st["value"] =str( stval )
    #
    #                     else:
    #                         pass
    #                         #p.pop("stoichiometry", None)
    #
    #                     if stmin is not None and stmax is not None:
    #                         st["minValue"] = str(stmin)
    #                         st["maxValue"] = str(stmax)
    #                     else:
    #                         pass
    #                         #p.pop("stoichiometryRange", None)

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
