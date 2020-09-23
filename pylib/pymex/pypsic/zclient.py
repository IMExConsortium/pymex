import sys
import json
import re

import ssl
import urllib
from http.client import HTTPSConnection, HTTPResponse
from requests import Session
from requests.auth import HTTPBasicAuth

from io import StringIO
from lxml import etree as ET

import pymex.pypsic

class Client():

    def __init__( self, mode='dev', debug=False ):
        self.mode = mode
        self.debug = debug

        self.ns = { 'reg' :"http://hupo.psi.org/psicquic/registry" }
        self.registryUrl = "http://www.ebi.ac.uk/Tools/webservices/psicquic/registry/registry?action=STATUS&format=xml"
        self.services = None
        self.default = "IMEx"

    @property                   
    def registry( self ):

        if self.services is not None:
            return self.services
                
        try:
            scontext = ssl.SSLContext(ssl.PROTOCOL_SSLv23)
            with urllib.request.urlopen( self.registryUrl,
                                         context=scontext ) as f:

                record = f.read().decode('utf-8')
                record = re.sub(r'<\?xml[^>]+>', '', record)

                parser = ET.XMLParser( remove_blank_text=True )
                dom = ET.parse(StringIO(record), parser)

                slst = dom.xpath( '//reg:service', namespaces = self.ns )

                services = {}
                
                for s in slst:
                    srv = {}
                    srv['name'] = s.xpath( './reg:name/text()',
                                           namespaces = self.ns )[0]
                    srv['rurl'] = s.xpath( './reg:restUrl/text()',
                                           namespaces = self.ns )[0]
                    srv['active'] = s.xpath( './reg:active/text()',
                                             namespaces = self.ns )[0]                    
                                        
                    services[ srv['name'].lower() ] = srv                    
                self.services = services
                
        except Exception as e:
            print( e )
            return None
        
        return pypsic.Registry( self.services )
        
    def getinteractor( self, query, server="DEFAULT",
                       first = 0, max = 10, format="xml25" ):
         
        if self.services is None:
            print("#Getting registry")
            self.registry

        if self.services is None:
            sys.exit(1)
            
        if server in ['DEFAULT']:        
            server = self.default

        print("#PSICQUC Server: " + server )
        
        if self.services is None or server.lower() not in self.services:
            sys.exit(1)

        if self.services[server.lower()]['active'].lower() == 'false':
            print("#PSICQUC Server not active")
            sys.exit(1)

        baseUrl = self.services[server.lower()]['rurl']    
        try:
            url = baseUrl +'interactor/' + query
            par = {'firstResult': first, 'maxResults': max, 'format': format}
            urlpar = urllib.parse.urlencode( par )            
            
            scontext = ssl.SSLContext(ssl.PROTOCOL_SSLv23)
            with urllib.request.urlopen( url + "?" + urlpar,
                                         context=scontext) as f:
                record = f.read().decode('utf-8')

            return record

        except Exception as e:
             print( e )
                   
        return None

    def getinteraction( self, query, server="DEFAULT",
                        first = 0, max = 10, format="xml25" ):
        
        if self.services is None:
            print("#Getting registry")
            self.registry

        if server in ['DEFAULT']:        
            server = self.default

        print("###PSICQUC Server: " + server )
        
        if self.services is None or server.lower() not in self.services:
            sys.exit(1)

        if self.services[server.lower()]['active'].lower() == 'false':
            print("#PSICQUC Server not active")
            sys.exit(1)

        baseUrl = self.services[server.lower()]['rurl']    
        
        try:

            url = baseUrl +'interaction/' + query
            par = {'firstResult': first, 'maxResults': max, 'format': format}
            urlpar = urllib.parse.urlencode( par )            

            print(url + "?" + urlpar)
            scontext = ssl.SSLContext(ssl.PROTOCOL_SSLv23)
            with urllib.request.urlopen( url + "?" + urlpar,
                                         context=scontext) as f:
                record = f.read().decode('utf-8')

            return record

        except Exception as e:
             print( e )
                   
        return None

    def getquery( self, query, server="DEFAULT",
                  first = 0, max = 10, format="xml25" ):

        if self.services is None:
            print("##Getting registry")
            self.registry
            
        if server in ['DEFAULT']:        
            server = self.default

        print("#PSICQUC Server: " + server )
         
        if self.services is None or server.lower() not in self.services:
            sys.exit(1)

        if self.services[server.lower()]['active'].lower() == 'false':
            print("#PSICQUC Server not active")
            sys.exit(1)

        baseUrl = self.services[server.lower()]['rurl']    
        
        try:

            url = baseUrl +'query/' + urllib.parse.quote(query)             
            par = {'firstResult': first, 'maxResults': max, 'format': format}
            urlpar = urllib.parse.urlencode( par )            
            print(url + "?" + urlpar)
            scontext = ssl.SSLContext(ssl.PROTOCOL_SSLv23)
            with urllib.request.urlopen( url + "?" + urlpar,
                                         context=scontext ) as f:
                record = f.read().decode('utf-8')

            return record

        except Exception as e:
             print( e )
                   
        return None
