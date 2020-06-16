import sys

from http.client import HTTPSConnection, HTTPResponse
import json
import re
import ssl

from requests import Session
from requests.auth import HTTPBasicAuth

import zeep
from zeep import Client as zClient, Settings as zSettings
from zeep.transports import Transport

from lxml import etree as ET

class Client():
    
    def __init__( self, user='', password='', server='', debug=False ):
        self.user = user
        self.password = password
        self.mode = server
        self.debug = debug

        if server in ['DEFAULT']:
            self.mode = ''
            
        if server == 'dev':
            url = 'http://10.1.200.100:8080/service/ws-v20?wsdl'
        else:
            url = 'https://imexcentral.org/icentral' + self.mode + '/service/ws-v20?wsdl'
            
        if self.debug:
            print(url)
            print(self.user)
            print(self.password)

        print(url)
        
        self.zsettings = zSettings(strict=False, xml_huge_tree=True)

        self.zsession = Session()
        if user != '':
            self.zsession.auth = HTTPBasicAuth(self.user, self.password) 

        self.zclient = zClient(url,
                               settings=self.zsettings,
                               transport=Transport(session=self.zsession))
        
        self.zfactory = self.zclient.type_factory('ns0')
        
        if self.debug:
            print(self.zclient)
            print("\nDONE: __init__") 

    def getstatus( self, depth='fill' ):
        
        try:
            srv = self.zclient.service
            record_found = srv.getServerStatus( depth )
            return record_found

        except Exception as e:
            print(e)
            print( " Status not avilable" )
            return {}

        
    def queryPublication( self, query='*', firstRec=1, max=10 ):
        
        try:
            srv = self.zclient.service
            print(query)
            record_found = srv.queryPublication( query=query,
                                                 firstRec=firstRec,
                                                 maxRec=max)
            return record_found
        
        except Exception as e:
            print(e)
            print( " Publication query failed" )
            return {}
        
    def queryAttachment( self, query='*', firstRec=1, max=10 ):
        
        try:
            srv = self.zclient.service
            record_found = srv.queryAttachment( query=query,
                                                firstRec=firstRec,
                                                maxRec=max )
            return record_found

        except Exception as e:
            print(e)
            print( " Attachment query failed" )        
            return {}
    
    def getentry( self, pmid ):
        
        ident = self.zfactory.identifier(ns= 'pmid',ac= pmid.rstrip())
        
        try:
            srv = self.zclient.service
            record_found =srv.getPublicationById( identifier=ident )            
            return record_found
        except Exception as e:
            print(e)
            print( "PMID:"+ str(pmid) + " Record not found" )
            return {}

    def getalist( self, pmid ):
        
        ident = self.zfactory.identifier(ns= 'pmid',ac= pmid.rstrip())
        
        try:
            srv = self.zclient.service            
            alist = srv.getAttachmentByParent(parent=ident)
            return alist
        except Exception as e:            
            print( e )
            return {}

    def addentry( self, pmid ):
        ident = self.zclient.factory.create('identifier')
        ident._ns= 'pmid'
        ident._ac= pmid

        record_added = {}

        try:
            srv = self.zclient.service
            record_added = srv.createPublicationById( ident )
            
            if self.debug:
                print( record_added )
        
        except Exception as e:
             print( e )

        if self.debug:
            print(self.zclient)
            print("\nDONE: addentry")

        return record_added

    def addatt( self, pmid, type='txt/comment', subject='', body='' ):
        ident = self.zclient.factory.create('identifier')

        ident._ns= 'pmid'
        ident._ac= pmid.rstrip()

        natt = self.zclient.factory.create('attachment')
        
        natt['_type'] = type
        natt['subject'] = subject
        natt['body'] = body
               
        try:
            srv = self.zclient.service
            attachment_added = srv.addAttachment( parent=ident,
                                                  attachment=natt)
            if self.debug:
                print( attachment_added )
        except Exception as e:            
            print( e )

    def addgrp( self, pmid, group):
        ident = self.zclient.factory.create('identifier')

        ident._ns= 'pmid'
        ident._ac= pmid.rstrip()
        
        try:
            print( " adding group: ", group)
            srv = self.zclient.service
            group_added = srv.updatePublicationAdminGroup( identifier=ident,
                                                           operation='add',
                                                           group=group )
            if self.debug:
                print( group_added )
            
        except Exception as e:            
            print( e )
                        
    def setstat( self, pmid, status):
        ident = self.zclient.factory.create('identifier')

        ident._ns= 'pmid'
        ident._ac= pmid.rstrip()
               
        try:
            print( " updating status to: ", status)
            srv = self.zclient.service
            status_updated = srv.updatePublicationStatus( identifier=ident,
                                                          status=status )
            if self.debug:
                print( status_updated )
            
        except Exception as e:            
            print( e )
        
        
    
