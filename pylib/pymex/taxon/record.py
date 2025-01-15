# -*- coding: utf-8 -*-
"""
Created on Tue Jan 14 09:05:33 2025

@author: lukasz
"""

import os
import pymex

from urllib.request import urlopen, Request
from lxml import etree as ET
from pymex import xmlrecord

class Record(xmlrecord.XmlRecord):
    """NCBI taxon record representation. Inherits XML parsing and serialization from xml.XmlRecord"""

    def __init__(self, root=None, debug=False):
        
        myDir = os.path.dirname( os.path.realpath(__file__))
        self.taxdbConfig = { "taxdb": { "IN": os.path.join( myDir, "defParse.json") } }
        
        self.url="https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=%%DB%%&id=%%ACC%%&rettype=xml&retmode=text"

        super().__init__( root,
                          config = self.taxdbConfig,
                          postproc = {"_global": self.globpost },
                          debug = debug )

    def getRecord(self, ac="9606"):
        curl = self.url.replace( "%%ACC%%", ac ).replace( "%%DB%%", 'taxonomy' )
        #print(curl)
        if self.debug:
            print("DEBUG: Record.getRecord: url->", curl)

        headers = { 'Accept': 'text/xml' }
        method = 'GET'
        body =''
        
        req = Request(curl)        
        res = self.parseXml( urlopen( req ), debug=self.debug)
            
        return( res )


    def parseXml(self, filename, ver="taxdb", debug=False):

        if self.debug:
            print("DEBUG: Record.parseXml: called")
        
        self.recordTree = ET.parse(filename)
        #print(ET.tostring(self.recordTree,pretty_print=True).decode())
        if self.debug:
            print("DEBUG: Record.parseXmlrecordTree:", self.recordTree)
        
        
        res =  super().parseXml2( ver=ver, debug=self.debug )        
        if '_global' in self.postproc:
            self.postproc['_global']()
        
        return res
        
    def parseHGNC(self, filename, ver="hgnc", debug=False):
        return self.parseXml( filename, ver=ver )

    def toHGNC( self, ver='hgnc' ):
        """Builds MIF elementTree from a Record object."""
        return None

    def globpost(self):
        if self.debug:
            print("DEBUG: Record.globpost: called")
        # build feature key map
        if self.record == None:
            return
        
        if 'feature' in self.record and self.record['feature'] != None:
            fbk = {}
            self.record["_feature_by_key"] = fbk
            #self.record["_feature"] = []
            fbk =  self.record["_feature_by_key"] 
            for f in self.record['feature']:
                ckey= f['key']
                
                #cf = pymex.Feature(f)
                fbk.setdefault(ckey,[]).append(f)
                #self.record["_feature"].append(cf)
            


    def rank(self, rank=None):
        """Taxonomic rank"""
        if rank == None:
            return self.root['lineage']

        for r in self.root['lineage']:
            if r['rank'] == rank:
                return r['sci-name']
        return  None
                
    @property
    def record(self):
        if 'GBSet' in self.root and len(self.root['GBSet']) > 0:
            return self.root['GBSet'][0]['GBSeq']
        else:
            return None
        
    @property
    def lineageSimple(self):
        """Returns simplified taxon lineage"""        
        return self.root['lineage-simple']

    @property
    def lineage(self, rank=None ):
        """Returns taxon lineage"""
        if rank == None:
            return self.root['lineage']

        for r in self.root['lineage']:
            if r['rank'] == rank:
                return r
        return  None
    
    @property    
    def primaryAc(self):
        """Returns the primary accession of the record"""

        if self.record != None and 'accession-primary' in self.record:
            return self.record['accession-primary']
        else:
            return None

    @property
    def secondaryAcLst(self):
        """Returns secondary accessions of the record"""
        if 'accession-secondary' in self.record:
            return  self.record['accession-secondary']
        else:
            return None
        
    @property
    def keywordLst(self):
        """Returns keywords"""
        if 'keyword' in self.record:
            return  self.record['omim_id'][0]
        else:
            return None
        
    @property
    def featureLst(self):
        """Returns a list of record features"""
        if '_feature' in self.record:
            return  self.record['feature']
        else:
            return None
        
    def getFeatureLstByKey( self, key ):

        if '_feature_by_key' in self.record:
            fbk = self.record['_feature_by_key']
            if  key in fbk:  
                return fbk[key]

        return None
