import os

from urllib.request import urlopen
import pymex

class UniRecord( pymex.xmlrecord.XmlRecord ):
    def __init__(self, root=None):
        myDir = os.path.dirname( os.path.realpath(__file__))
        self.uniConfig = { "uni_v001": {"IN": os.path.join( myDir, "defUniParse_v001.json"),
                                        "OUT": os.path.join( myDir, "defUniXml_v001.json" ) }
        }
                
        self.url="https://www.uniprot.org/uniprot/%%ACC%%.xml"
    
        super().__init__(root, config=self.uniConfig,
                         process = { "comconv": self.comconv ,
                                     "geneName": self.geneName  })
        
    def parseXml(self, filename, ver="uni_v001", debug=False):
        res =  super().parseXml( filename, ver=ver )
                
        return res

    def comconv( self, elem, rec ):
        print("comconv: elem=", elem)
        print("comconv: rec.keys=",list(rec.keys()))
                         
    def geneName( self, elem, rec ):
        print("geneName: elem=", elem)
        print("geneName: rec.keys=",list(rec.keys()))
        if "name" in rec:
            print(rec["name"])
                         
    def getRecord(self, ac="P60010"):
        upUrl = self.url.replace( "%%ACC%%", ac )                

        res = self.parseXml( urlopen(upUrl ))
        self.record = res
        return( res )

    @property
    def entry( self ): 
         return self.root["uniprot"]["entry"][0]
