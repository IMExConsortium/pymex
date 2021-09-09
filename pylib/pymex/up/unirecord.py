import os

from urllib.request import urlopen
import pymex

class UniRecord( pymex.xmlrecord.XmlRecord ):
    def __init__(self, root=None):
        myDir = os.path.dirname( os.path.realpath(__file__))
        self.uniConfig = { "uni_v001": {"IN": os.path.join( myDir, "defUniParse_v001.json"),
                                        "OUT": os.path.join( myDir, "defUniXml_v001.json" ) }
        }

        self.debug = False
        self.url="https://www.uniprot.org/uniprot/%%ACC%%.xml"
    
        super().__init__(root, config=self.uniConfig,
                         process = { "geneName": self.geneName,
                                     "protName": self.protName,
                                     "accession": self.accession,
                                     "comment": self.comment,
                                     "xref": self.xref,
                                     "feature": self.feature})
        
    def parseXml(self, filename, ver="uni_v001", debug=False):
        res =  super().parseXml( filename, ver=ver )
                
        return res
        
    def protName( self, elem, rec ):
        if self.debug:
            print("protName: elem=", elem)
            print("protName: rec.keys=",list(rec.keys()))        
 
        if "protein" in rec:
            print(rec["protein"])

            protein = rec["protein"]
            rec["_protein"] = {"name":{}}

            #print("CN", )
            
            for cname in protein:
                if "recommendedName" == cname:                     
                    rec["_protein"]["name"]["rec"]={}
                    if  "fullName" in protein[cname]:
                        rec["_protein"]["name"]["rec"]["full"] =  protein[cname]["fullName"]
                    if  "shortName" in protein[cname]:
                        rec["_protein"]["name"]["rec"]["short"] =  protein[cname]["shortName"]
                        
                elif "alternativeName" == cname:

                    for altname in protein[cname]:                        
                        if "alt" not in rec["_protein"]["name"]:
                            rec["_protein"]["name"]["alt"]=[]
                        
                        calt = {}     
                        if "fullName" in altname :
                            calt["full"] = altname["fullName"]
                        if "shortName" in altname:
                            calt["short"] = altname["shortName"]
                        rec["_protein"]["name"]["alt"].append( calt ) 
                        
                       
    def geneName( self, elem, rec ):
        if self.debug:
            print("geneName: elem=", elem)
            print("geneName: rec.keys=",list(rec.keys()))        
        if "gene" in rec:
            #print(rec["gene"])

            gene = rec["gene"]
            rec["_gene"] = {"name":{}}

            for cgene in gene["name"]:
                cval  = cgene["value"]
                ctype = cgene["type"]

                #print("CN",ctype,cval)
                
                if ctype not in rec["gene"]["name"]:
                    if ctype != "primary":
                        rec["_gene"]["name"][ctype]=[]
                    else:
                        rec["_gene"]["name"][ctype]=cval

                if ctype != "primary":
                    rec["_gene"]["name"][ctype].append(cval)
                    

    def accession( self, elem, rec ):
        if "_accession" not in rec:
            rec["_accession"]={"primary":None}
            
        if rec["_accession"]["primary"] is None:
            rec["_accession"]["primary"] = rec["accession"][-1]
        else:
            if "secondary" not in rec["_accession"]:
                rec["_accession"]["secondary"] = []
            rec["_accession"]["secondary"].append(rec["accession"][-1])
                
    def comment( self, elem, rec ):
        if self.debug:
            print("TYPE:",rec["comment"][-1]["type"])
        ccom = rec.setdefault("_comment",{})
        ctp = ccom.setdefault(rec["comment"][-1]["type"],[])
        ctp.append( rec["comment"][-1] )    
            
    def xref( self, elem, rec ):
        if self.debug:
            print("XREF TYPE:",rec["dbReference"][-1]["type"])
        ccom = rec.setdefault("_xref",{})
        ctp = ccom.setdefault(rec["dbReference"][-1]["type"],[])
        ctp.append( rec["dbReference"][-1] )    

    def feature( self, elem, rec ):
        if self.debug:
            print("FEATURE TYPE:",rec["feature"][-1]["type"])
        ccom = rec.setdefault("_feature",{})
        ctp = ccom.setdefault(rec["feature"][-1]["type"],[])
        ctp.append( rec["feature"][-1] )    
            
    def getRecord(self, ac="P60010"):
        upUrl = self.url.replace( "%%ACC%%", ac )                

        res = self.parseXml( urlopen(upUrl ))
        self.record = res
        return( res )

    @property
    def entry( self ): 
         return self.root["uniprot"]["entry"][0]
     
    @property
    def accession(self):
        return self.root["uniprot"]["entry"][0]["_accession"]
     
    @property
    def name( self ):
        return self.root["uniprot"]["entry"][0]["name"]

    @property
    def protein( self ):
        return self.root["uniprot"]["entry"][0]["_protein"]

    @property
    def gene( self ):
        return self.root["uniprot"]["entry"][0]["_gene"]

    @property
    def xref( self ):
        return self.root["uniprot"]["entry"][0]["_xref"]

    @property
    def feature( self ):
        return self.root["uniprot"]["entry"][0]["_feature"]
     
