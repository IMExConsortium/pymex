from http.client import HTTPSConnection, HTTPResponse
import json
import re
import ssl

from requests import Session
from requests.auth import HTTPBasicAuth

from zeep import Client as zClient, Settings as zSettings
from zeep.transports import Transport

from lxml import etree as ET

class Client():
 
    def __init__( self, user='guest', password='guest',
                  mode='dev', debug=False ):

        self.dxfns = { 'dxf': 'http://dip.doe-mbi.ucla.edu/services/dxf14' }

        self.user = user
        self.password = password
        self.mode = mode
        self.debug = debug
                
        url = 'https://dip.mbi.ucla.edu/dip-legacy/dxf?wsdl'
 
        if mode == 'dev':
            url = 'https://dip.mbi.ucla.edu/dip-legacy/dxf?wsdl'
            
        if self.debug:
            print(url)
            print(self.user)
            print(self.password)

        self._zsettings = zSettings(strict=False, xml_huge_tree=True)

        self._zsession = Session()
        
        self._zsession.verify = False
        # self._zsession.auth = HTTPBasicAuth(self.user, self.password) 

        self._zclient = zClient(url,
                               settings=self._zsettings,
                               transport=Transport(session=self._zsession))
        
        self._dxfactory = self._zclient.type_factory('ns1')
        self._ssfactory = self._zclient.type_factory('ns0')
        
        if self.debug:
            print(self.zclient)
            print("\nDONE: __init__") 

    @property
    def dxf(self): 
        return self._dxfactory

    @property
    def ssf(self):
        return self._ssfactory

    def getnode( self, ns, ac, detail='default', format='dxf14' ):
        print("LEGPYClinet: getnode")
        client = self._zclient                 
        try:
            with client.settings(raw_response=True):
                node = self._zclient.service.getNode( ns = ns, ac = ac,
                                                      detail='default',
                                                      format='dxf14')
                tree = ET.fromstring(node.text)
                dset = tree.xpath('//dxf:dataset',namespaces = self.dxfns )
                if dset:
                    return dset[0]
        except Exception as e:
             print( e )
        return None

    def getlink( self, ns, ac, detail='default', format='dxf14' ):
        print("LEGPYClinet: getlink")
        client = self._zclient
        try:
            with client.settings(raw_response=True):
                link = client.service.getLink( ns = ns, ac = ac,
                                               detail=detail,
                                               format='dxf14')
                tree = ET.fromstring(link.text)                
                dset = tree.xpath('//dxf:dataset',namespaces = self.dxfns )
                if dset:
                    return dset[0]
        except Exception as e:
             print( e )
        return None

    def getsource( self, ns, ac, detail='default', format='dxf14' ):
        print("LEGPYClinet: getsource")
        client = self._zclient
        try:
            with client.settings(raw_response=True):
                source = client.service.getSource( ns = ns, ac = ac,
                                                   detail=detail,
                                                   format='dxf14')
                tree = ET.fromstring(source.text)
                dset = tree.xpath('//dxf:dataset',namespaces = self.dxfns )
                if dset:
                    return dset[0]
        except Exception as e:
             print( e )
        return None

    def getevid( self, ns, ac, detail='default', format='dxf14' ):
        print("LEGPYClinet.getevid: detail=" + detail)
        client = self._zclient
        try:
            with client.settings(raw_response=True):
                evid = client.service.getEvidence( ns = ns, ac = ac,
                                                   detail=detail,
                                                   format='dxf14')
                tree = ET.fromstring(evid.text)
                dset = tree.xpath('//dxf:dataset',namespaces = self.dxfns )
                if dset:
                    return dset[0]
        except Exception as e:
             print( e )
        return None

    

