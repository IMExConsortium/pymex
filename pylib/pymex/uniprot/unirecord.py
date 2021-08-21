import os

from urllib.request import urlopen
import pymex

print("UniRecord: import")

class UniRecord( pymex.xmlrecord.XmlRecord ):
    def __init__(self, root=None):
        myDir = os.path.dirname( os.path.realpath(__file__))
        self.uniConfig = { "uni001": {"IN": os.path.join( myDir, "defUniParse001.json"),
                                      "OUT": os.path.join( myDir, "defUniParse001.json" ) }
        }

        self.url="https://www.uniprot.org/uniprot/%%ACC%%.xml"

        super().__init__(root, config=self.uniConfig )

    def parseXml(self, filename, ver="uni001", debug=False):
        res =  super().parseXml( filename, ver=ver )
        print(res)

        return res

    def getRecord(self, ac="P60010"):
        upUrl = self.url.replace( "%%ACC%%", ac )

        res = self.parseXml( urlopen(upUrl ))
        return( res )

    def addFeatureEvidence(self, parameter1, parameter2):
        return
