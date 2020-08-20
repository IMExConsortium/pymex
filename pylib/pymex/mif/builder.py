import json
import sys
import os
import re
from lxml import etree
from urllib.request import urlopen

import pymex

class RecordBuilder():

    def __init__(self,debug=False):
        self.debug = debug
        self.oboUrl = 'https://www.ebi.ac.uk/ols/api/ontologies/mi/terms?iri=http://purl.obolibrary.org/obo/'
        self.taxUrl = 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=taxonomy&retmode=xml&id='
        self.uniNs = { "up":"http://uniprot.org/uniprot" }
        self.uniUrl = 'https://www.uniprot.org/uniprot/'
        self.cvreg = re.compile("([^:]+:\d+)(\(.+\))?")
        self.cvtrec = {}
        self.taxrec = {}
        self.unirec = {}

        self.feature = False 
        
        self.template = {}
        self.cvdict = {}

        self.root = []
        self.pdir = os.path.dirname( os.path.realpath(__file__) )
        
        srcpath = os.path.join( self.pdir,'jmif-source.jmif' )
        self.template["source"] = json.load( open( srcpath, 'r' ) )["source"]

        cvtpath = os.path.join( self.pdir,'jmif-cvterm.jmif' )
        self.cvdict = json.load( open( cvtpath, 'r' ) )

    def cvterm( self, cvid ):
        
        cvmatch = self.cvreg.match( cvid )
        if cvmatch:
            cvid = cvmatch.group(1)
        else:
            cvid = self.cvdict[cvid]

        if cvid not in self.cvtrec:

            #fetch term from OLS
            
            cvurl = self.oboUrl + cvid.replace(':','_')
            jcv = json.load( urlopen( cvurl ) )
            term = {}
            term['label'] = jcv['_embedded']['terms'][0]['label']
            term['def'] = jcv['_embedded']['terms'][0]['annotation']['definition'][0]
            term['id'] = jcv['_embedded']['terms'][0]['obo_id']

            self.cvtrec[ term['id'] ] = term 

        return self.cvtrec[cvid]

    def buildCvTerm( self, cvid ):
        
        term = self.cvterm( cvid )

        res = { "names": { "shortLabel": term["label"] },
                "xref": {
                    "primaryRef": self.buildXref( term["id"],
                                                  db="psi-mi",
                                                  dbAc= "MI:0488") } }
        return res

    def buildXref( self, acc, db="uniprotkb", dbAc="MI:0486", version = None,
                   refType="identity", refTypeAc="MI:0356" ):
    
        res = { "db": db, "dbAc": dbAc, "id": acc,                
                "refType": refType, "refTypeAc": refTypeAc }                    

        if version is not None: 
            res["version"] = irec["version"]

        return res
    
    def taxon(self, taxid):

        if taxid not in self.taxrec:
            tax = {}

            taxurl = self.taxUrl + taxid

            print(taxurl)
            taxpath = "/TaxaSet/Taxon[./TaxId/text()="+taxid+"]"
            record = etree.parse( urlopen( taxurl ) )
            trec = record.xpath(taxpath )

            if trec:
                tax['taxid'] = taxid 
                sname = trec[0].xpath("./OtherNames/CommonName/text()")
                lname = trec[0].xpath("./ScientificName/text()") 

                if lname:
                    tax['lname'] = lname[0]
            
                if sname:
                    tax['sname'] = sname[0]
                else:
                    tax['sname'] = tax['lname']
                
                self.taxrec[ taxid ] = tax
                
        return self.taxrec[ taxid ]
        
    def uniprot(self, acc):

        if acc not in self.unirec:
            uprot = {}
        
            uniurl = self.uniUrl + acc +".xml"

            print(uniurl)
            accpath = "/up:uniprot/up:entry/up:accession/text()"
            verpath = "/up:uniprot/up:entry/@version"
            snamepath = "/up:uniprot/up:entry/up:name/text()"
            lnamepath = "/up:uniprot/up:entry/up:protein/up:recommendedName/up:fullName/text()"
            taxpath = "/up:uniprot/up:entry/up:organism/up:dbReference[./@type='NCBI Taxonomy']/@id"
            record = etree.parse( urlopen( uniurl ) )
        
            uacc = record.xpath( accpath, namespaces = self.uniNs )
            if uacc:
                uprot["acc"] = str( uacc[0] )

            version = record.xpath( verpath, namespaces = self.uniNs )
            if version:
                uprot["version"] = str( version[0] )
           
            sname = record.xpath( snamepath,namespaces = self.uniNs )            
            if sname:
                uprot["sname"] = str( sname[0] ) 
                                
            lname = record.xpath( lnamepath, namespaces = self.uniNs )
            if lname:
                uprot["lname"] = str( lname[0] ) 

            taxid = record.xpath( taxpath, namespaces = self.uniNs )
            if taxid:
                uprot["taxid"] = str( taxid[0]  )
                
            self.unirec[acc] = uprot
        
        return self.unirec[acc]
        

    def build( self, filename ):    
        
        record = {}
        source = None
        interaction = None
        participant = None
        feature = None
        frange = None
        print(filename)
        print(os.getcwd())
        with open( filename, 'r' ) as sf:
            for ln in sf:
                ln = ln.strip()
                
                if ln.startswith("source"):
                    self.feature = False
                    record["source"] = {}
                    (foo, src) = ln.split("\t")
                    
                    if src in self.template["source"]:
                        record["source"] =  self.template["source"][src]
                        
                elif ln.startswith("interaction"):
                    self.feature = False
                    interaction =  {"names":{"shortLabel": "N/A"},
                                    "experimentList":[{"names":{"shortLabel": "N/A"}}]}
                    record.setdefault("interactionList",[]).append(interaction)
                    
                    cols = ln.split("\t")

                    # interaction type 
                    interaction["interactionType"] = self.buildCvTerm(cols[1])
                    
                    # interaction detection                 
                    interaction["experimentList"][0]["interactionDetectionMethod"] = self.buildCvTerm(cols[2])
                                        
                    # interaction host 
                    
                    for taxid in cols[3:]:                                                
                        ctax = self.taxon( taxid )
                        
                        interaction["experimentList"][0].setdefault("hostOrganism",[]).append( {                    
                            "names": {
                                "shortLabel": ctax["sname"],
                                "fullName": ctax["lname"] },
                            "taxid": ctax["taxid"] } )
                        
                elif ln.startswith("molecule"):
                    self.feature = False
                    participant = {}
                    interaction.setdefault( "participantList",[] ).append( participant )

                    # interactor 
                    interactor = {}
                    participant["interactor"] = interactor 
                                        
                    cols = ln.split("\t")
                                        
                    if cols[2].startswith("uprot:"):
                        (acc,ver) = (cols[2].split(".") + [""])[0:2]                        
                        irec = self.uniprot( acc.replace("uprot:","") )
                        if len(ver) > 0:
                            irec["version"] = ver
                    else:
                        pass

                    # interactor names
                    
                    interactor["names"] = { "shortLabel":irec["sname"].lower(),
                                            "fullName":irec["lname"] }
                    
                    # interactor primary ref
                    xref = {}
                    interactor.setdefault("xref",xref) 
                    xref["primaryRef"] = self.buildXref( irec["acc"],
                                                         db="uniprotkb",
                                                         dbAc= "MI:0486" )
                    
                    #interactor type
                    interactor["interactorType"] = self.buildCvTerm( cols[1] )

                    # interactor organism                    
                    ctax = self.taxon( irec["taxid"] )
                                                           
                    interactor["organism"] = {                    
                        "names": {
                            "shortLabel": ctax["sname"],
                            "fullName": ctax["lname"] },
                        "taxid": irec["taxid"] }
                                        
                    # participant names
                    participant["names"] = {"shortLabel":irec["sname"].lower()}
       
                    # host                     
                    if len(cols) > 4:
                        hostOrganism = []
                        participant["hostOrganism"] = hostOrganism 
                        
                        for taxid in cols[4:]:                        
                            taxon = self.taxon( taxid )

                            ctax = {"shortLabel":taxon["sname"],
                                    "fullName":taxon["lname"],
                                    "taxid":taxon["taxid"]}
                            
                            hostOrganism.append(ctax)

                    #stoichiometry
                    catt = { "value":"Stoichiometry: " + cols[3],
                             "name":"comment",
                             "nameAc":"MI:0612" }
                    participant.setdefault( "attributeList", [] ).append(catt)                                                
                            
                elif ln.startswith("exprole"):
                    self.feature = False            
                    participant.setdefault("exproleList",[])
                    
                    cols = ln.strip().split("\t")                    
                    for role in cols[1:]:                        
                        roleCv = self.cvterm( role )
                        participant["exproleList"].append( self.buildCvTerm( role ) )

                elif ln.startswith("biorole"):
                    self.feature = False            
                    participant.setdefault("bioroleList",[])
                    
                    cols = ln.split("\t")
                    for role in cols[1:]:                    
                        participant["bioroleList"].append( self.buildCvTerm( role ) )
                        
                elif ln.startswith("idmethod"):
                    
                    if self.feature:
                        idmethod = feature.setdefault( "idmethod",[] )
                    else:                        
                        idmethod = participant.setdefault( "idmethodList",[] )

                    cols = ln.split("\t")
                    for mth in cols[1:]:                        
                        idmethod.append( self.buildCvTerm( mth ) )
                                                
                elif ln.startswith("feature"):
                    self.feature = True
                    feature = {}
                    participant.setdefault("featureList",[]).append( feature )

                    cols = ln.strip().split("\t")                
                    feature["featureType"] = self.buildCvTerm( cols[1] )

                    if len(cols) > 2:
                        feature["names"] = {}
                        feature["names"]["shortLabel"] = cols[2]
                        if len(cols) > 3:
                            feature["names"]["fullName"] = cols[3]
                        else:
                            pass
                    else:
                        pass
                    
                elif ln.startswith("range"):
                    self.feature = True
                    if "range" not in feature:
                        feature["featureRange"] = []
                    frange = {}
                    feature["featureRange"].append(frange)

                    cols = ln.strip().split("\t")
                    rbegin = cols[1]
                    rend = cols[2]

                    if '..' in rbegin:
                        frange["startStatus"] = self.buildCvTerm( "MI:0338" ) #range
                        (sbeg,ebeg) = rbegin.split('..')
                        frange["begin"]={"start": sbeg , "end": ebeg}
                        
                    elif rbegin in ['n','c']:
                        frange["begin"] = { "position": "0" }

                        if rbegin == 'n':
                            frange["beginStatus"] = self.buildCvTerm( "MI:0340" ) # n-term                            
                        else:
                            frange["beginStatus"] = self.buildCvTerm( "MI:0334" ) # c-term
                    else:
                        frange["startStatus"] = self.buildCvTerm( "MI:0335" ) # certain
                        frange["begin"]={ "position": rbegin }
                    
                    if '..' in rend:
                        frange["endStatus"] = self.buildCvTerm( "MI:0338" ) #range
                        (sbeg,ebeg) = rbegin.split('..')
                        frange["end"]={"start": sbeg , "end": ebeg}

                    elif rend in ['n','c']:
                        frange["end"]={ "position": "0" }

                        if rend == 'n':
                            frange["endStatus"] = self.buildCvTerm( "MI:0340" ) # n-term                            
                        else:
                            frange["endStatus"] = self.buildCvTerm( "MI:0334" ) # c-term
                    else:
                        frange["endStatus"] = self.buildCvTerm( "MI:0335" ) # certain
                        frange["end"]={ "position": rend }                                       
                    
                elif ln.startswith("#"):
                    self.feature = False
                    interaction = None
                    participant = None
                    feature = None
                    frange = None
        return pymex.mif254.Mif254Record( [record] )
