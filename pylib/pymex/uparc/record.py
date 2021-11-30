import os

from urllib.request import urlopen
import pymex

class Record( pymex.xmlrecord.XmlRecord ):
    def __init__(self, root=None):
        myDir = os.path.dirname( os.path.realpath(__file__))
        self.uniConfig = { "uni_v001": {"IN": os.path.join( myDir, "defUniParse_v001.json"),
                                        "OUT": os.path.join( myDir, "defUniXml_v001.json" ) }
        }

        self.debug = False
        self.url="https://www.uniprot.org/uniparc/%%ACC%%.xml"
        self.qurl="https://www.uniprot.org/uniparc?format=xml&query=%%ACC%%"

        self._pdef = None
        
        super().__init__( root, config=self.uniConfig )
        
    def parseXml(self, filename, ver="uni_v001", debug=False):
        res =  super().parseXml( filename, ver=ver )
                
        return res

    def query(self, query="A8A1Q4"):
        upUrl = self.qurl.replace( "%%ACC%%", query )                

        res = self.parseXml( urlopen(upUrl ))
        self.record = res
        return( res )
            
    def getRecord(self, ac="UPI00005F1659"):
        upUrl = self.url.replace( "%%ACC%%", ac )                
    
        res = self.parseXml( urlopen(upUrl ))
        self.record = res
        return( res )
                                          
    @property
    def entry( self ): 
        return self.root["uniparc"]["entry"][0]
     
    @property
    def copyright(self):
        return self.root["uniparc"]["copyright"]

    @property
    def accession(self):
        return self.root["uniparc"]["entry"][0]["accession"]

    @property
    def sequence(self):
        return self.root["uniparc"]["entry"][0]["sequence"]

    @property
    def dbRef(self):
        return self.root["uniparc"]["entry"][0]["dbReference"]

    @property
    def elist(self):
        elist =[]
        for e in self.root["uniparc"]["entry"]:
            elist.append(Entry(e))
        return elist
    
class Entry:

    def __init__(self, entry):
        self.root = entry

    @property
    def accession(self):
        return self.root["accession"]

    @property
    def sequence(self):
        return self.root["sequence"]

    @property
    def dbRef(self):
        return self.root["dbReference"]
    
        

    
