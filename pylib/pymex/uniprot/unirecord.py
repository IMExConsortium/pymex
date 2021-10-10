import os

from urllib.request import urlopen
import pymex
from lxml import etree as ET

print("UniRecord: import")

class UniRecord( pymex.xmlrecord.XmlRecord ):
    def __init__(self, root=None):
        myDir = os.path.dirname( os.path.realpath(__file__))
        self.uniConfig = { "uni001": {"IN": os.path.join( myDir, "defUniParse001.json"),
                                      "OUT": os.path.join( myDir, "defUniParse001.json" ) }
        }

        self.url="https://www.uniprot.org/uniprot/%%ACC%%.xml"
        #{evidence key: dbReference element}
        self.evidence = {}
        super().__init__(root, config=self.uniConfig )

    def parseXml(self, filename, ver="uni001", debug=False):



        self.recordTree = ET.parse(filename)
        self.preprocessComments(ver)


        res =  super().parseXml2(ver=ver )
        #print(res)

        #change to Record class function - postprocess()
        for x in self.postprocess:

            #finding all evidence elements
            if x.tag[-8:] == "evidence":
                print("this evidence")
                parentElem = self.postprocess[x][1]
                elem = x
                eval(self.postprocess[x][0])

            else:
                print(x.tag[-8:])
                print("not evidence")

        #appending appropriate evidence elements to all feature elements
        for x in self.postprocess:

            if x.tag[-7:] == "feature":
                print("this feature")
                parentElem = self.postprocess[x][1]
                elem = x
                eval(self.postprocess[x][0])
            else:
                print(x.tag[-7:])
                print("not feature")

        #re-parsing newly edited tree
        #res2 = super().parseXml2(ver=ver)

        print(res)


        return res


    def preprocessComments(self, ver):
        #uses self.recordTree ElementTree object to modify the element tree into separate comments of different types
        for comment in self.recordTree.iter("{http://uniprot.org/uniprot}comment"):
            print(comment.tag)
        return

    def getRecord(self, ac="P60010"):
        upUrl = self.url.replace( "%%ACC%%", ac )

        res = self.parseXml( urlopen(upUrl ))
        return( res )

    def addToFeature(self, featureElem):
        if "evidence" in featureElem.attrib:
            featureEvidence = featureElem.attrib["evidence"]
            #add multiple evidence here
            if featureEvidence in self.evidence:
                evidence = self.evidence[featureEvidence]
                if evidence is not None:
                    print("ADDING EVIDENCE")
                    featureElem.append(evidence)
                else:
                    print("No evidence")
        return

    def addEvidence(self, evidenceElem):

        evidenceKey = evidenceElem.attrib["key"]
        allContents = evidenceElem.findall(".//*")
        if (len(allContents) > 1):

            dbReference = allContents[-1]
            print(dbReference)
            self.evidence[evidenceKey] = dbReference
        else:
            self.evidence[evidenceKey] = None

        return
