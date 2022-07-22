import os

import pymex

class Record( pymex.xmlrecord.XmlRecord ):
    def __init__(self, root=None):
        myDir = os.path.dirname( os.path.realpath(__file__))
        self.uniConfig = { "clinvar_v001": {"IN": os.path.join( myDir, "defClinVarParse_v001.json"),
                                            "OUT": os.path.join( myDir, "defClinVarXml_v001.json" ) }
        }

        self.debug = False

        self._pdef = None
        
        super().__init__( root, config=self.uniConfig,
                          postproc = { } )
        
    def parseXml( self, filename, ver="clinvar_v001", debug=False ):
        res =  super().parseXml( filename, ver=ver )
                
        return res

    def parseXmlStr( self, xmlstr, ver="clinvar_v001", debug=False ):
        res =  super().parseXmlStr( xmlstr, ver=ver )
                
        return res

    def parseXmlTree( self, xmltree, ver="clinvar_v001", debug=False ):
        res =  super().parseXmlTree( xmltree, ver=ver )
                
        return res

    @property
    def result(self):
        """Returns query result"""
        return self.root['response']['result']

print("pymex.clinvar: loaded")
