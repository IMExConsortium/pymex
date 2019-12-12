from http.client import HTTPSConnection, HTTPResponse
import json
import re
import ssl

import urllib.request

from requests import Session
from requests.auth import HTTPBasicAuth

class Client():

    def __init__( self, mode='dev', debug=False ):
        self.mode = mode
        self.debug = debug

        self.baseUrl = 'https://dip.mbi.ucla.edu/dip-proxy/ws/rest/proxy-service/dxf-record'
        self.pubmedUrl = self.baseUrl + '/NCBI/pubmed/'
        
        #  pmid/30753612?detail=full'
        
    def getpubmed( self, pmid, detail='full', format='dxf15' ):
        try:
            url = self.pubmedUrl +'pmid/' + pmid +'?detail='+ detail
            scontext = ssl.SSLContext(ssl.PROTOCOL_SSLv23)
            with urllib.request.urlopen(url, context=scontext) as f:
                record = f.read().decode('utf-8')

            return record

        except Exception as e:
             print( e )
                   
        return None
        

        
        
    
