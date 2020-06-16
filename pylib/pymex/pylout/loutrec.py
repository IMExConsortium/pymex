import os
import sys
import json
import copy 
import pylout

from lxml import etree as ET

class LOutRecordList():
    """  Representation of LinOut records.
    """
    def __init__( self, dxf=None, root=None ):
        print( "init called" )
        self.template = "recordinfo-template.xml"
        self.pylout_home = os.path.dirname( pylout.__file__ )

        template_file = open( os.path.join( self.pylout_home , self.template) )
        parser = ET.XMLParser(remove_blank_text=True)

        self.rlist = ET.parse( template_file, parser )
        
        lset = self.rlist.xpath('//LinkSet')
        self.rset = lset[0]

        llst = self.rlist.xpath('//LinkSet/Link')        
        
        for el in llst:
            lset[0].remove( el )
            self.rlink = el
            
        print(ET.tostring(self.rlist))
        #print(ET.tostring( self.rlist ) )

    def appendLink( self, linkid, imexid, pmid, curation='' ):
        
        clink = copy.deepcopy( self.rlink )

        # linkid
        
        clid = clink.xpath('.//*[contains(text(),"%%LINKID%%")]')
        for id in clid:
            id.text = id.text.replace( "%%LINKID%%", linkid ) 

        # imexid

        cpmid = clink.xpath('.//*[contains(text(),"%%IMEXID%%")]')
        for id in cpmid:
            id.text = id.text.replace( "%%IMEXID%%", linkid ) 

        # pmid

        cpmid = clink.xpath('.//*[contains(text(),"%%PMID%%")]')
        for id in cpmid:
            id.text = id.text.replace( "%%PMID%%", pmid ) 

        # curation

        ccur = clink.xpath('.//*[contains(text(),"%%CURATION%%")]')        
        for cur in ccur:
            cur.text = cur.text.replace( "%%CURATION%%", curation )

        self.rset.append( clink )


    def toXML(self):
        return ET.tostring( self.rlist, pretty_print=True )
