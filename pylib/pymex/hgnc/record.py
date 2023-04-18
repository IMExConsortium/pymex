# -*- coding: utf-8 -*-
"""
Created on Wed Apr 18 09:05:33 2023

@author: lukasz
"""

import os
import pymex

from urllib.request import urlopen, Request
from lxml import etree as ET
from pymex import xmlrecord

class HgncRecord(xmlrecord.XmlRecord):
    """HGNC record representation. Inherits XML parsing and serialization from xml.XmlRecord"""

    def __init__(self, root=None):

        myDir = os.path.dirname( os.path.realpath(__file__))
        self.hgncConfig = { "hgnc": { "IN": os.path.join( myDir, "defParse.json") } }

        self.url="https://rest.genenames.org/fetch/symbol/%%ACC%%"

        super().__init__( root,
                          config = self.hgncConfig,
                          postproc = {} )

    def getRecord(self, ac="ZNF3"):
        curl = self.url.replace( "%%ACC%%", ac )
        #print(curl)

        headers = { 'Accept': 'text/xml' }
        method = 'GET'
        body =''
        
        req = Request(curl)
        #print(req.get_method())
        #print(req.header_items())
        req.add_header('Accept', "text/xml" )
        
        res = self.parseXml( urlopen( req ))
        return( res )


    def parseXml(self, filename, ver="hgnc", debug=False):
        
        self.recordTree = ET.parse(filename)

        #print(ET.tostring(self.recordTree, pretty_print=True).decode())

        
        res =  super().parseXml2(ver=ver )
        
        return res
        
    def parseHGNC(self, filename, ver="hgnc", debug=False):
        return self.parseXml( filename, ver=ver )

    def toHGNC( self, ver='hgnc' ):
        """Builds MIF elementTree from a Record object."""
        return None

    @property
    def record(self):
        return self.root['response']['result']['doc']
    
    @property
    def symbol(self):
        """Returns record (gene) symbol"""        
        return self.record['symbol']
    
    @property    
    def uprAc(self):
        """Returns the first UniprotKB accession of the record"""

        if 'uniprot_ids' in self.record:
            return self.record['uniprot_ids'][0]
        else:
            return None

    @property
    def entrezId(self):
        """Returns Entrez Id of the record"""
        if 'entrez_ids' in self.record:
            return  self.record['entrez_id']
        else:
            return None
        
    @property
    def omimId(self):
        """Returns first OMIM  Id of the record"""
        if 'omim_ids' in self.record:
            return  self.record['omim_id'][0]
        else:
            return None

        
    @property
    def omimIdLst(self):
        """Returns a list of OMIM Ids of the record"""
        if 'omim_ids' in self.record:
            return  self.record['omim_id']
        else:
            return None

