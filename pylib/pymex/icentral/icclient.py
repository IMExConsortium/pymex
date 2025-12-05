from http.client import HTTPSConnection, HTTPResponse
import json
import re
import ssl

from requests import Session
from requests.auth import HTTPBasicAuth

#import zeep as Z

from zeep import Client as zClient
from zeep import Settings as zSettings
from zeep.transports import Transport

from lxml import etree as ET

from pathlib import Path

class ICentralClient():
 
    def __init__( self, user='', password='',
                  mode='dev', debug=False ):

        self.ns = { 'dxf': 'http://dip.doe-mbi.ucla.edu/services/dxf20',
                    'i':"http://imex.mbi.ucla.edu/icentral/ws"}
        self.user=''
        self.password=''

        if len(user) > 0:
            self.user = user
            
        
        if len( password) > 0:
            self.password = password
            
        
        self.mode = mode
        self.debug = debug    
  
        url = 'https://imexcentral.org/icentralbeta/service/ws-v20?wsdl'
       
        if mode == 'dev':
            url = 'https://imexcentral.org/icentralbeta/service/ws-v20?wsdl'
             
        if self.debug:
            print(url)
            print(self.user)
            print(self.password)

        self._zsettings = zSettings(strict=False, xml_huge_tree=True)

        self._zsession = Session()
        
        #self._zsession.verify = False
        self._zsession.auth = HTTPBasicAuth(self.user, self.password) 

        self._zclient = zClient(url,
                               settings=self._zsettings,
                               transport=Transport(session=self._zsession))
        
        #self._dxfactory = self._zclient.type_factory('ns1')
        #self._ssfactory = self._zclient.type_factory('ns0')
        
        if self.debug:
            print(self.zclient)
            print("\nDONE: __init__") 

    @property
    def client(self): 
        return self._zclient

    @property
    def dxf(self): 
        return self._dxfactory

    @property
    def ssf(self):
        return self._ssfactory


    def getServerStatus(self, depth):
        
        client = self._zclient                 
        try:
            with client.settings(raw_response=True):
                node = self._zclient.service.getServerStatus( '' )
                
                tree = ET.fromstring(node.text)

                #plst = tree.xpath('//i:publication',namespaces=self.ns)

                print(ET.tostring(tree,pretty_print=True).decode())

        except Exception as e:
            print( e )
        return None

            
    def getPubById( self, ns, ac ):
        print("ICentral Client: getPubById")

        client = self._zclient                 
        try:
            with client.settings(raw_response=True):
                node = self._zclient.service.getPublicationById(identifier={ 'ns': ns,
                                                                            'ac': ac} )
                
                tree = ET.fromstring(node.text)

                plst = tree.xpath('//i:publication',namespaces=self.ns)

                #print(ET.tostring(tree,pretty_print=True).decode())
                #
                #for p in plst:
                #    print(ET.tostring(p,pretty_print=True).decode())

                return plst 
                    
        except Exception as e:
             print( e )
        return None
        
    def getPubByStatus( self, status,firstrec,maxrec ):
        print("ICentral Client: getPubByStatus")

        client = self._zclient                 
        try:
            with client.settings(raw_response=True):
                node = self._zclient.service.getPublicationByStatus(status='RELEASED',
                                                                    firstRec=firstrec,
                                                                    maxRec=maxrec)
                
                tree = ET.fromstring(node.text)
                
                plist = tree.xpath('.//i:publication',namespaces=self.ns)
                plast = tree.xpath('.//i:lastRec/text()',namespaces=self.ns)
                
                #print(ET.tostring(tree,pretty_print=True).decode())
                
                #for p in plst:
                #    print(ET.tostring(p,pretty_print=True).decode())


                print(len(plist))
                
                return (plast[0],plist)
                    
        except Exception as e:
             print( e )
        return None
        
    def rec2linkout(self, rec):

        cdir = Path( __file__ ).parent.absolute()

        try:
            lo = ''
  
            plst = rec.xpath('.//i:identifier[@ns="pmid"]/@ac',namespaces=self.ns)
            ilst = rec.xpath('.//i:imexAccession/text()',namespaces=self.ns)
            #print(plst)        
            with open(str(cdir)+'/record-template.xml','r') as rth:
                for ln in rth:

                    ln = ln.replace('%%LINK_ID%%',plst[0])
                    ln = ln.replace('%%RULE%%',ilst[0])
                    
                    lo+=ln
        
            return lo
                
        except Exception as e:
            print( e )
            print(ET.tostring(rec,pretty_print=True).decode())            
            return ''


    
    def lowrap(self):
        cdir = Path( __file__ ).parent.absolute()
        lw =''

        with open(str(cdir)+'/record-list.xml','r') as rlh:
            for ln in rlh:
                lw+=ln

        return lw
print("pymex.icentral.ICentralClient: loaded")


    
