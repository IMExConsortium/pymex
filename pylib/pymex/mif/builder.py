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
        self.oboUrl = 'https://www.ebi.ac.uk/ols/api/ontologies/%CVT%/terms?iri=http://purl.obolibrary.org/obo/'
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
            cvlabel = None
        else:
            try:
                cvid = self.cvdict[cvid]
                cvlabel = None
            except:
                cvlabel = cvid
                cvid = None
            
        if cvlabel is not None:
            term = {"label" : cvlabel }
            return term
        
        if cvid not in self.cvtrec:

            #fetch term from OLS

            cvc = cvid.split(":")
            
            cvurl = self.oboUrl.replace("%CVT%",cvc[0].lower()) + cvid.replace(':','_')            
            jcv = json.load( urlopen( cvurl ) )
            
            term = {}
            term['label'] = jcv['_embedded']['terms'][0]['label']
            
            if "description" in jcv['_embedded']['terms'][0]:
                 term['def'] = jcv['_embedded']['terms'][0]["description"]
                 
            elif "definition" in jcv['_embedded']['terms'][0]['annotation']:
                term['def'] = jcv['_embedded']['terms'][0]['annotation']['definition'][0]
                
            term['id'] = jcv['_embedded']['terms'][0]['obo_id']

            try:
                term["dbac"]=self.cvdict[cvc[0].lower()]["dbac"]
                term["db"]=self.cvdict[cvc[0].lower()]["db"]
            except:
                term["dbac"]=None
                term["db"]=None
            self.cvtrec[ term['id'] ] = term 
        
        return self.cvtrec[cvid]

    def buildCvTerm( self, cvid ):
        
        term = self.cvterm( cvid )

        res = { "names": { "shortLabel": term["label"] } }

        if "id" in term:
            
            res["xref"] = { "primaryRef": self.buildXref( term["id"],
                                                          db=term["db"],
                                                          dbAc= term["dbac"]) }
        return res

    def buildXref( self, acc, db="uniprotkb", dbAc="MI:0486", version = None,
                   refType="identity", refTypeAc="MI:0356" ):
    
        res = { "id": acc, "refType": refType, "refTypeAc": refTypeAc }                    

        if db is not None:
            res["db"] = db
            
        if dbAc is not None:
            res["dbAc"] = dbAc 
        
        if version is not None: 
            res["version"] = version

        return res
    
    def taxon(self, taxid):
        
        if taxid in ["-1","in vitro"]:
            tax = {"lname":"in vitro","sname":"in vitro","taxid":"-1"}
            self.taxrec[ "-1" ] = tax
            taxid = "-1"
        if taxid not in self.taxrec:
            tax = {}

            taxurl = self.taxUrl + taxid
            
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
        interactor = None
        participant = None
        feature = None
        frange = None
        xtgt = None
        seqtgt = None
        bibref = None

        with open( filename, 'r' ) as sf:
            for ln in sf:
                ln = ln.strip()
                col = [s.strip() for s in ln.strip().split("\t")]
                
                if ln.startswith("source"):
                    self.feature = False
                    
                    record["source"] = {}
                    src = col[1]
                    if src in self.template["source"]:
                        record["source"] =  self.template["source"][src]
                    xtgt = record["source"]

                elif ln.startswith("pmid"):
                    pmid = col[1]
                    pref = self.buildXref( pmid, db="pubmed", dbAc="MI:0446",
                                           refType="primary-reference", refTypeAc="MI:0358" )    
                    bibref = {"xref":{"primaryRef": pref}}
                    
                elif ln.startswith("interaction"):
                    self.feature = False
                    interaction =  {"names":{"shortLabel": "N/A"},
                                    "experiment":[{"names":{"shortLabel": "N/A"}}]}
                    if bibref is not None:
                        interaction["experiment"][0]["bibref"] = bibref
                    
                    record.setdefault("interaction",[]).append(interaction)
                    
                    # interaction type 
                    interaction["interactionType"] = self.buildCvTerm(col[1])
                    
                    # interaction detection                 
                    interaction["experiment"][0]["interactionDetectionMethod"] = self.buildCvTerm(col[2])

                    # participant identification

                    interaction["experiment"][0]["participantIdentificationMethod"] = self.buildCvTerm("experimental particp") 
                    
                    # interaction host 

                    taxid =  col[3]                
                    ctax = self.taxon( taxid )

                    interaction["experiment"][0].setdefault("hostOrganism",[]).append( {                    
                        "names": {
                            "shortLabel": ctax["sname"],
                            "fullName": ctax["lname"] },
                        "ncbiTaxId": ctax["taxid"] } )
                    
                    if len(col) > 4:
                        ctype = self.buildCvTerm( col[4] )
                        if ctype is not None:
                            interaction["experiment"][0]["hostOrganism"][0]["cellType"] = ctype

                    if len(col) > 5:
                        compartnent = self.buildCvTerm( col[5] )
                        if compartnent is not None:
                            interaction["experiment"][0]["hostOrganism"][0]["compartment"] = compartnent

                    if len(col) > 6:
                        tissue = self.buildCvTerm( col[6] )
                        if tissue is not None:
                            interaction["experiment"][0]["hostOrganism"][0]["tissue"] = tissue
                        
                    xtgt = interaction    
                elif ln.startswith("molecule"):
                    self.feature = False
                    participant = {}
                    interaction.setdefault( "participant",[] ).append( participant )

                    # interactor 
                    interactor = {}
                    participant["interactor"] = interactor 
                                                                                
                    if col[2].startswith("uprot:"):
                        (acc,ver) = (col[2].split(".") + [""])[0:2]                        
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
                    interactor["interactorType"] = self.buildCvTerm( col[1] )

                    # interactor organism                    
                    ctax = self.taxon( irec["taxid"] )
                                                           
                    interactor["organism"] = {                    
                        "names": {
                            "shortLabel": ctax["sname"],
                            "fullName": ctax["lname"] },
                        "ncbiTaxId": irec["taxid"] }

                    xtgt = participant["interactor"]
                    # participant names
                    participant["names"] = {"shortLabel":irec["sname"].lower()}
       
                    # host                     
                    if len(col) > 4:
                        hostOrganism = []
                        participant["hostOrganism"] = hostOrganism 

                        taxid =  col[4]
                        ctax = self.taxon( taxid )

                        hostOrganism.append( {
                            "names": {
                                "shortLabel": ctax["sname"],
                                "fullName": ctax["lname"] },
                            "ncbiTaxId": ctax["taxid"] } )

                        if len(col) > 5:
                            ctype = self.buildCvTerm( col[5] )
                            if ctype is not None:
                                hostOrganism[0]["cellType"] = ctype

                        if len(col) > 6:
                            compartnent = self.buildCvTerm( col[6] )
                            if compartnent is not None:
                                hostOrganism[0]["compartnent"] = compartnent

                        if len(col) > 7:
                            tissue = self.buildCvTerm( col[7] )
                            if tissue is not None:
                                hostOrganism[0]["tissue"] = tissue

                    #stoichiometry
                    catt = { "value":"Stoichiometry: " + col[3],
                             "name":"comment",
                             "nameAc":"MI:0612" }
                    participant.setdefault( "attribute", [] ).append(catt)                                                

                    # seq target

                    seqtgt = participant["interactor"]
                    
                elif ln.startswith("exprole"):
                    self.feature = False            
                    participant.setdefault("experimentalRole",[])
                    
                    for role in col[1:]:                                            
                        participant["experimentalRole"].append( self.buildCvTerm( role ) )

                elif ln.startswith("expprep"):                    
                    self.feature = False            
                    participant.setdefault("experimentalPreparation",[])                    
                    for prep in col[1:]:                                                
                        participant["experimentalPreparation"].append( self.buildCvTerm( prep ) )                    
                elif ln.startswith("biorole"):
                    self.feature = False            
                    participant.setdefault("biologicalRole",[])
                    
                    for role in col[1:]:                    
                        participant["biologicalRole"].append( self.buildCvTerm( role ) )
                        
                elif ln.startswith("idmethod"):                                        
                    if self.feature:                        
                        mthCV = self.buildCvTerm( col[1].strip() )
                        feature["featureDetectionMethod"] = mthCV
                    else:
                        participant.setdefault("participantIdentificationMethod",[])
                        for mth in col[1:]:
                            mthCV = self.buildCvTerm( mth )
                            participant["participantIdentificationMethod"].append( mthCV )
                                                
                elif ln.startswith("feature"):
                    self.feature = True
                    feature = {}
                    participant.setdefault("feature",[]).append( feature )

                    feature["featureType"] = self.buildCvTerm( col[1] )

                    if len(col) > 2:
                        feature["names"] = {}
                        feature["names"]["shortLabel"] = col[2]
                        if len(col) > 3:
                            feature["names"]["fullName"] = col[3]
                        else:
                            pass
                    else:
                        pass
                    
                    xtgt = feature
                    
                elif ln.startswith("range"):
                    self.feature = True
                    if "range" not in feature:
                        feature["featureRange"] = []
                    frange = {}
                    feature["featureRange"].append(frange)

                    seqtgt = frange

                    rbegin = col[1]
                    rend = col[2]

                    if '..' in rbegin:
                        frange["startStatus"] = self.buildCvTerm( "MI:0338" ) #range
                        (sbeg,ebeg) = rbegin.split('..')
                        frange["begin"]={"start": sbeg , "end": ebeg}
                        
                    elif rbegin in ['n','c']:
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
                        #frange["end"]={ "position": "0" }

                        if rend == 'n':
                            frange["endStatus"] = self.buildCvTerm( "MI:0340" ) # n-term                            
                        else:
                            frange["endStatus"] = self.buildCvTerm( "MI:0334" ) # c-term
                    else:
                        frange["endStatus"] = self.buildCvTerm( "MI:0335" ) # certain
                        frange["end"]={ "position": rend }                                       

                elif ln.startswith("xref"):                    
                    db = col[1]
                    acc = col[2]
                    if len(col) > 3:
                        xtype = col[3]
                    else:
                        xtype = "identity"

                    if len(col) > 4:
                        dbac = col[4]
                    else:
                        dbac = self.cvdict[db]

                    if len(col) > 5:
                        xtypeac = col[5]
                    else:
                        xtypeac = self.cvdict[xtype]                    
                    
                    ver = None
                    if '.' in acc:
                        ver = acc[acc.rfind('.')+1:]
                        acc = acc[0:acc.rfind('.')]
                        if len(ver) == 0:
                            ver = None

                    if col[0].endswith(".p"):
                        xtgt = record["participant"]
                    
                    xref =  self.buildXref( acc, db=db, dbAc=dbac, version = ver,
                                            refType=xtype, refTypeAc=xtypeac )

                    if "xref" not in xtgt:                    
                        xtgt["xref"] = {}

                    if "primaryRef" not in xtgt["xref"]:
                        xtgt["xref"]["primaryRef"] = xref
                    else:
                        if "secondaryRef" not in xtgt["xref"]:
                            xtgt["xref"]["secondaryRef"] = []
                        xtgt["xref"]["secondaryRef"].append(xref)
                        
                elif ln.startswith("figure"):                
                    flabel = col[1]
                    if "atrribute" not in interaction:
                        interaction["attribute"]= []
                    att = {"name":"figure legend", "nameAc":"MI:0599","value":flabel}
                    interaction["attribute"].append(att)

                elif ln.startswith("seq"):                    
                    seq = col[1].upper()
                    if len(col) > 2:
                        nseq = col[2].upper()           
            
                    if "startStatus" in seqtgt:  # seqtgt is range                    
                        seqtgt["sequence"] = {}
                        seqtgt["sequence"]["original"]=seq
                        seqtgt["sequence"]["new"]=nseq
                        
                    else:
                        seqtgt["sequence"] = seq
                                            
                elif ln.startswith("#"):
                    self.feature = False
                    interaction = None
                    participant = None
                    feature = None
                    frange = None
                    seqtgt = None

        return pymex.mif.Record( {"entrySet":{ "entry":[record] } } )
