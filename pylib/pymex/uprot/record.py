import os
import re

from urllib.request import urlopen
import pymex
import json

class Record( pymex.xmlrecord.XmlRecord ):
    def __init__(self, root=None):
        myDir = os.path.dirname( os.path.realpath(__file__))
        self.uniConfig = { "uni_v001": {"IN": os.path.join( myDir, "defUniParse_v001.json"),
                                        "OUT": os.path.join( myDir, "defUniXml_v001.json" ) }
        }

        self.debug = False
        self.url="https://www.uniprot.org/uniprot/%%ACC%%.xml"

        self._pdef = None
        
        super().__init__( root, config=self.uniConfig,
                          postproc = { "geneName": self._geneName,
                                       "protName": self._protName,
                                       "accession": self._accession,
                                       "comment": self._comment,
                                       "xref": self._xref,
                                       "feature": self._feature})
        
    def parseXml(self, filename, ver="uni_v001", debug=False):
        res =  super().parseXml( filename, ver=ver )
                
        return res

    def getRecord(self, ac="P60010"):
        upUrl = self.url.replace( "%%ACC%%", ac )                

        res = self.parseXml( urlopen(upUrl ))
        self.record = res
        return( res )
    
    def _protName( self, elem, rec, cval ):
        if self.debug:
            print("protName: elem=", elem)
            print("protName: rec.keys=",list(rec.keys()))        
 
        if "protein" in rec:
            protein = rec["protein"]
            rec["_protein"] = {"names":{}}    
            for cname in protein:
                if "recommendedName" == cname:                     
                    rec["_protein"]["names"]["rec"]={}
                    if  "fullName" in protein[cname]:
                        rec["_protein"]["names"]["rec"]["full"] =  protein[cname]["fullName"]
                        rec["_protein"]["names"]["fullName"] =protein[cname]["fullName"]
                    if  "shortName" in protein[cname]:
                        rec["_protein"]["names"]["rec"]["short"] =  protein[cname]["shortName"]
                        rec["_protein"]["names"]["shortLabel"] =  protein[cname]["shortName"]
                elif "alternativeName" == cname:
                    for altname in protein[cname]:                        
                        if "alt" not in rec["_protein"]["names"]:
                            rec["_protein"]["names"]["alt"]=[]
                        
                        calt = {}     
                        if "fullName" in altname :
                            calt["full"] = altname["fullName"]
                            rec["_protein"]["names"].setdefault("alias",[]).append(altname["fullName"])
                        if "shortName" in altname:
                            calt["short"] = altname["shortName"]
                            rec["_protein"]["names"].setdefault("alias",[]).append(altname["shortName"])
                        rec["_protein"]["names"]["alt"].append( calt )
                elif "submittedName" == cname:
                    rec["_protein"]["names"]["sub"]={}
                        
                    if "fullName" in protein[cname] :
                        rec["_protein"]["names"]["sub"]["full"] =  protein[cname]["fullName"]
                        #rec["_protein"]["names"]["fullName"] =protein[cname]["fullName"]
                            
                    if "shortName" in protein[cname]:
                        rec["_protein"]["names"]["sub"]["short"] =  protein[cname]["shortName"]
                        #rec["_protein"]["names"]["shortLabel"] =  protein[cname]["shortName"]    
                                                
                   
                                               
    def _geneName( self, elem, rec, cval ):
        if self.debug:
            print("geneName: elem=", elem)
            print("geneName: rec.keys=",list(rec.keys()))        
        if "gene" in rec:
            gene = rec["gene"]
            rec["_gene"] = {"name":{}}

            for cgene in gene["name"]:
                cval  = cgene["value"]
                ctype = cgene["type"]
                
                if ctype not in rec["_gene"]["name"]:
                    if ctype != "primary":                        
                        rec["_gene"]["name"][ctype]=[]
                    else:
                        rec["_gene"]["name"][ctype]=cval

                if ctype != "primary":
                    rec["_gene"]["name"][ctype].append(cval)                    

    def _accession( self, elem, rec, cval ):
        if "_accession" not in rec:
            rec["_accession"]={"primary":None}
            
        if rec["_accession"]["primary"] is None:
            rec["_accession"]["primary"] = rec["accession"][-1]
        else:
            if "secondary" not in rec["_accession"]:
                rec["_accession"]["secondary"] = []
            rec["_accession"]["secondary"].append(rec["accession"][-1])
                
    def _comment( self, elem, rec, cval ):
        if self.debug:
            print("TYPE:",rec["comment"][-1]["type"])
        ccom = rec.setdefault("_comment",{})
        ctp = ccom.setdefault(rec["comment"][-1]["type"],[])
        ctp.append( rec["comment"][-1] )

        #print("_comment: cval !!! ", cval.keys())
        if "text" in cval and "evidence" in cval["text"]:
            #print("!!!")
            #print( "_comment: evidence", cval["evidence"].split() )

            cevid =rec["comment"][-1].setdefault("_evidence",[])
            
            #print( self.root["uniprot"]["entry"][0].keys())
            if "evidence" not in self.root["uniprot"]["entry"][0]:
                self.root["uniprot"]["entry"][0]["evidence"]={}
                
            for eid in cval["text"]["evidence"].split(" "):
                if eid not in self.root["uniprot"]["entry"][0]["evidence"]:
                    self.root["uniprot"]["entry"][0]["evidence"][eid]= {}
                rec["comment"][-1]["_evidence"].append(self.root["uniprot"]["entry"][0]["evidence"][eid])
             
        #print("_comment: cval", cval,"\n")
         
                    
            
    def _xref( self, elem, rec, cval ):
        if self.debug:
            print("XREF TYPE:",rec["dbReference"][-1]["type"])
        ccom = rec.setdefault("_xref",{})
        ctp = ccom.setdefault(rec["dbReference"][-1]["type"],[])
        ctp.append( rec["dbReference"][-1] )    
 
    def _feature( self, elem, rec, cval ):
        if self.debug:
            print("FEATURE TYPE:",rec["feature"][-1]["type"])
        ccom = rec.setdefault("_feature",{})

        #print(" LEN FEATURE:", len(rec["feature"]) )
        
        if rec["feature"][-1]["type"] == "sequence variant":
            ntp = "variant"
        elif rec["feature"][-1]["type"] == "mutagenesis site":
            ntp = "mutation"
        else:
            ntp = rec["feature"][-1]["type"]
            
        ctp = ccom.setdefault(ntp,[])
        ctp.append( rec["feature"][-1] )    

        if "id" in rec["feature"][-1]:

            xreflist = rec["feature"][-1].setdefault("xref", [] )
            xreflist.append({"type":"uprv","id":rec["feature"][-1]["id"]})
            
        
        if "description" in rec["feature"][-1] and "dbSNP:rs" in rec["feature"][-1]["description"]:
            rs = re.sub(".*dbSNP:","", rec["feature"][-1]["description"])
            rs = re.sub( "\..*","",rs)
            
            xreflist = rec["feature"][-1].setdefault("xref", [] )
            xreflist.append( {"type":"dbSNP","id":rs} )
        
        if "evidence" in cval:            
            cevid =rec["feature"][-1].setdefault("_evidence",[])
            
            if "evidence" not in self.root["uniprot"]["entry"][0]:
                self.root["uniprot"]["entry"][0]["evidence"]={}
                
            for eid in cval["evidence"].split():
                if eid not in self.root["uniprot"]["entry"][0]["evidence"]:
                    self.root["uniprot"]["entry"][0]["evidence"][eid]= {}
                rec["feature"][-1]["_evidence"].append(self.root["uniprot"]["entry"][0]["evidence"][eid])
          
        if "variation" in rec["feature"][-1] and len(rec["feature"][-1]["variation"]) > 1:
            # print( "  must clone ", rec["feature"][-1])
            # multiple sequence variation: must clone 
            multivar = list(rec["feature"][-1]["variation"])

            rec["feature"][-1]["variation"] = list(multivar[0])

            for i in range(1, len(multivar)):
                #print( " ", multivar[i] )
                nvar = {}
                for key in rec["feature"][-1].keys():
                    nvar[key]=rec["feature"][-1][key]
                nvar["variation"]=multivar[i]
                rec["feature"].append(nvar)
                ctp.append(nvar) 
            
        #print(" LEN FEATURE:", len(rec["feature"]),"\n")
        # dbSNP references
        
                      
    @property
    def entry( self ): 
         return self.root["uniprot"]["entry"][0]
     
    @property
    def accession(self):
        return self.root["uniprot"]["entry"][0]["_accession"]

    @property
    def acc(self):
        if "secondary" in self.accession:
            return pymex.Name( self.accession["primary"],
                               self.accession["secondary"] )
        else:
            return pymex.Name( self.accession["primary"],
                               None )
    @property
    def version(self):
        return self.root["uniprot"]["entry"][0]["version"]
     
    #@property
    #def name( self ):
    #    return self.root["uniprot"]["entry"][0]["name"]

    @property
    def name( self ):
        return { "entry": self.root["uniprot"]["entry"][0]["name"],
                 "protein": self.protein,
                 "gene": self.gene }
    
    @property
    def protein( self ):
        
        if self._pdef is not None:
            return pymex.Protein(self._pdef)
        if self.debug:
            print("building rec.protein")
        
        self._pdef = { "names":{"alias":[]},
                       "xref": [],
                       "interactorType": { "_names":{"shortLabel":"protein",
                                                     "fullName":"protein"},
                                           "_xref":{"primaryRef":{ "db":"psi-mi", "ac":"MI:0326" } } },
                       "organism": {"_names":{} },
                       "sequence": self.root["uniprot"]["entry"][0]["sequence"]["value"] }

        entry = self.root['uniprot']['entry'][0]
                
        #organism/host
        #-------------

        sciName=""
        comName=""
        taxid = ""
        for nme in entry["organism"]["name"]:
            if nme["type"]=="scientific":
                sciName=nme["value"]
            elif len(comName) == 0 and nme["type"]=="common":
                comName=nme["value"]

        if len(comName) == 0:
            comName=sciName

        for dbr in entry["organism"]["dbReference"]:
            if dbr["type"] == "NCBI Taxonomy":
                taxid=dbr["id"]
            
        org = {"_names":{"shortLabel":comName,
                         "fullName":sciName},
               "ncbiTaxId":entry["organism"]["dbReference"][0]["id"] }
        self._pdef["organism"]=org
        
        # names
        #------        

        prt = self.root['uniprot']['entry'][0]['_protein']
        names = prt['names']

        if "rec" in names:
            entry_name = names["rec"]
        elif "sub"  in names:
            entry_name = names["sub"]

        name = entry_name["full"]
        if "short" in entry_name.keys(): 
            label = entry_name["short"]
        elif "_gene" in entry and "name" in entry["_gene"] and "primary" in entry["_gene"]["name"]:
            label = entry["_gene"]["name"]["primary"]
        else:
            label = self.root['uniprot']['entry'][0]["name"]            
        
        alias = []
        if "gene" in prt.keys():
            for key in prt["gene"]["name"]:
                if "primary" != key:
                    for alias in  prt["gene"]["name"][key]:
                        pass
                        #print(alias)

        #protein name aliases
        if "names" in prt:
            if "alt" in prt["names"]:
                for p in prt["names"]["alt"]:
                    if "full" in p:
                        alias.append({"value":p["full"],"type":"protein name synonym"})
                    if "short" in p:
                        alias.append({"value":p["short"],"type":"protein name synonym"})
        
        # gene name aliases
        if "gene" in entry:
            for g in entry["gene"]["name"]:
                if g["type"] == "primary":
                    alias.append({"value":g["value"],"type":"gene name"})
                else:
                    alias.append({"value":g["value"],"type":"gene name synonym"})
                        
        self._pdef["names"]["shortLabel"]=label
        self._pdef["names"]["fullName"]=name
        self._pdef["names"]["alias"]=alias

        return pymex.Protein(self._pdef)

    @property
    def gene( self ):
        if "_gene" in self.root["uniprot"]["entry"][0]:
            return self.root["uniprot"]["entry"][0]["_gene"]
        return None
    
    @property
    def taxon( self ):
        return self.root["uniprot"]["entry"][0]["organism"]

    @property
    def xref( self ):
        if "_xref" in self.root["uniprot"]["entry"][0]:
            return self.root["uniprot"]["entry"][0]["_xref"]
        else:
             return None

    @property
    def feature( self ):
        if "_feature" in self.root["uniprot"]["entry"][0]:
            return self.root["uniprot"]["entry"][0]["_feature"]
        else:
            return None

    @property
    def feat( self ):

        entry = self.root["uniprot"]["entry"][0]
        if "_feature" not in entry:
            return {}            

        feat = {}
        
        for key in entry["_feature"]:
            #print("key", key)
            feat[key] = []
            for ff in entry["_feature"][key]:
                #print( " ",ff)
                feat[key].append(pymex.Feature( ff) )
        return feat
           
        #if "_feature" in self.root["uniprot"]["entry"][0]:
        #    return self.root["uniprot"]["entry"][0]["_feature"]
        #else:
        #    return None
     
    @property
    def comment( self ):
        if "_comment" in self.root["uniprot"]["entry"][0]:
            return self.root["uniprot"]["entry"][0]["_comment"]
        else:
            return None
     
    @property
    def comm( self ):

        entry = self.root["uniprot"]["entry"][0]
        if "_comment" not in entry:
            return {}

        comm = {}
            
        for key in entry["_comment"]:            
            comm[key] = []
            for cc in entry["_comment"][key]:
                comm[key].append(pymex.Comment( self.root, cc) )
        
        return comm
     
