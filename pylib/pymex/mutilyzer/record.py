import os

from urllib.request import urlopen
import pymex

class Record( pymex.xmlrecord.XmlRecord ):
    def __init__(self, root=None):
        myDir = os.path.dirname( os.path.realpath(__file__))
        self.uniConfig = { "mut_v001": {"IN": os.path.join( myDir, "defMutParse_v001.json"),
                                        "OUT": os.path.join( myDir, "defMutXml_v001.json" ) }
        }

        self.debug = False
        self.url="https://www.uniprot.org/uniprot/%%ACC%%.xml"

        self._pdef = None
        
        super().__init__( root, config=self.uniConfig,
                          postproc = { } )
        
    def parseXml( self, filename, ver="mut_v001", debug=False ):
        res =  super().parseXml( filename, ver=ver )
                
        return res

    def parseXmlStr( self, xmlstr, ver="mut_v001", debug=False ):
        res =  super().parseXmlStr( xmlstr, ver=ver )
                
        return res

    def parseXmlTree( self, xmltree, ver="mut_v001", debug=False ):
        res =  super().parseXmlTree( xmltree, ver=ver )
                
        return res

    @property
    def result(self):
        """Returns query result"""
        return self.root['response']['result']


    
print("pymex.mutilyzer: loaded")
