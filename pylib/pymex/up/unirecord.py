import os

from urllib.request import urlopen
from time import sleep
from pathlib import Path

import pymex

class UniRecord( pymex.xmlrecord.XmlRecord ):
    def __init__( self, root=None, url=None, mirror_xml=None, mirror_json=None ):
        myDir = os.path.dirname( os.path.realpath(__file__))
        self.uniConfig = { "uni_v001": {"IN": os.path.join( myDir, "defUniParse_v001.json"),
                                        "OUT": os.path.join( myDir, "defUniXml_v001.json" ) }
        }

        self.debug = False
        self._url="https://www.uniprot.org/uniprot/%%ACC%%.xml"

        self._mirror= { "xml": None,
                        "json": None}
        
        if url is not None:
            self._url= url

        if mirror_xml is not None:
            self._mirror['xml'] = mirror_xml
                        
        if mirror_json is not None:
            self._mirror['json'] = mirror_json

        
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

    #def getRecord(self, ac="P60010"):
    #    upUrl = self.url.replace( "%%ACC%%", ac )                
    #
    #    res = self.parseXml( urlopen(upUrl ))
    #    self.record = res
    #    return( res )


    def getRecord( self, eg, debug=False, delay=1 ):

        rec = self.getlocal( eg )
        
        if rec is None:
            rec = self.getremote( eg )
            sleep(delay)
        return rec

    def getfpath( self, acc ):
    
        cdir = ""
        pfix = self._mirror['xml'] + "/"
        eg = "0"*15+ str(acc)
        eg = eg[-15:]
        for i in range(0,12,3):
            cdir +=  "/" +eg[i:i+3]

        if self.debug:
            print("cdir",cdir)    
        fpath_local = pfix + "local" + cdir + "/" + acc + ".xml"
        
        if os.path.isfile( fpath_local ):
            return fpath_local

        
        fpath_trembl = pfix + "trembl" +  cdir + "/" + acc + ".xml"
        if self.debug:
            print("fpath_trembl",fpath_trembl)
        
        if os.path.isfile( fpath_trembl ):
            return fpath_trembl

        
        fpath_swp = pfix + "swissprot" + cdir + "/"+ acc + ".xml"
        if self.debug:
            print("fpath_swp",fpath_swp)    
        
        if os.path.isfile( fpath_swp ):
            return fpath_swp

        # create local directory
        
        Path( pfix + cdir + "/local/" ).mkdir(parents=True, exist_ok=True)
        if self.debug:
            print("getfpath(local):", fpath_local)
                
        return fpath_local


    def getlocal( self, eg ):

        rec = None

        fpath = self.getfpath( eg )

        #print("getlocal->fpath:", fpath)
        
        if fpath is None:
            return rec
        
        if os.path.isfile( fpath ):
            
            # parse xml

            rec = self.parseXml( fpath ) 
            
        return rec
    
    def getremote( self, eg ):
        #print("EntrezGene: get report")
        url = self._url.replace('%%ACC%%',eg)
        print(url)

        rec = {}
        
        #with open( self.getfpath( eg ), "w" ) as lf:
        #    for ln in urlopen(url):
        #        lf.write(ln.decode())
            
        
        # parse xml

        #rec = self.parseXml( self.getfpath( eg ) )
        rec = self.parseXml( urlopen(url) )
        
        return rec

    
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

        if rec["feature"][-1]["type"] == "sequence variant":
            ntp = "variant"
        elif rec["feature"][-1]["type"] == "mutagenesis site":
            ntp = "mutation"
        else:
            ntp = rec["feature"][-1]["type"]
            
        ctp = ccom.setdefault(ntp,[])
        ctp.append( rec["feature"][-1] )    
            
    @property
    def entry( self ): 
         return self.root["uniprot"]["entry"][0]
     
    @property
    def accession(self):
        return self.root["uniprot"]["entry"][0]["_accession"]
     
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
        
        self._pdef = { "names":{"alias":[]},
                       "xref": [],
                       "interactorType": { "_names":{"shortLabel":"protein",
                                                     "fullName":"protein"},
                                           "_xref":{"primaryRef":{ "db":"psi-mi", "ac":"MI:0326" } } },
                       "organism": {"_names":{} },
                       "sequence": self.root["uniprot"]["entry"][0]["sequence"]["value"] }

        # xrefs
        

        
        # names
        entry = self.root['uniprot']['entry'][0]
        prt = self.root['uniprot']['entry'][0]['_protein']
        names = prt['names']

        if "rec" in names:
            entry_name = names["rec"]
        elif "sub"  in names:
            entry_name = names["sub"]

        name = entry_name["full"]
               
        if "short" in entry_name.keys(): 
            label = entry_name["short"]
        elif "_gene" in entry:
            label = entry["_gene"]["name"]["primary"]
        else:
            label = self.root['uniprot']['entry'][0]["name"]
        
        prt_alias = []
        
        #for key in prt["names"]:
        #    pass
        
        alias = []
        if "gene" in prt.keys():
            for key in prt["gene"]["name"]:
                if "primary" != key:
                    for alias in  prt["gene"]["name"][key]:
                        print(alias)

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
        else:
            return {}
    @property
    def taxon( self ):
        return self.root["uniprot"]["entry"][0]["organism"]

    @property
    def xref( self ):
        return self.root["uniprot"]["entry"][0]["_xref"]

    @property
    def feature( self ):
        return self.root["uniprot"]["entry"][0]["_feature"]
     
    @property
    def comment( self ):
        return self.root["uniprot"]["entry"][0]["_comment"]
     
