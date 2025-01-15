import os
import sys

from urllib.request import urlopen
from time import sleep
import pymex
import json

class Record( pymex.xmlrecord.XmlRecord ):
 
    def __init__( self, root=None, mode='dev', debug=False ):

        myDir = os.path.dirname( os.path.realpath(__file__))
        self.config = { "eg001": {"IN": os.path.join( myDir, "proteomeParse001.json"),
                                  "OUT": os.path.join( myDir, "proteomeXml001.json" ) }
                       }
            
        super().__init__(root, config=self.config )
        
        self.mode = mode
        self._debug = debug    

        self._mirror= { "xml": '/mirror/uniprot/proteomes/xml',
                        "json": '/mirror/uniprot/proteomes/json'}
        self._url = 'https://www.ebi.ac.uk/interpro/api/entry/InterPro/protein/reviewed/%%ACC%%'
            
        if self._debug:        
            print("\nDONE: __init__") 
                   
        if self._debug:
            print( self._url)
            print(self._mirror)


    def _strand( self, elem=None, rec=None, cval=None ):

        print("ELEM", elem)
        print("REC", rec["strand"] )
        print("CCH(pre): ", cval.keys())
        if 'strand' in rec and "value" in rec["strand"]:
            rec["strand"] = rec["strand"]["value"]
                         

    def getfpath( self, eg, format="xml" ):

        file = eg +"." + format
        
        cdir = self._mirror[format]
        eg = "0"*12+ str(eg)
        eg = eg[-15:]
        for i in range(0,12,3):
            cdir +=  "/" +eg[i:i+3]
            if not os.path.isdir(cdir):
                os.mkdir(cdir) 

        fpath = cdir + "/" + file
        
        return fpath

            
    def getlocal( self, eg, format="xml", debug=False ):

        rec = None

        fpath = self.getfpath( eg, format )
        if debug:
            print(" fpath: ", fpath)
        
        if os.path.isfile( fpath ):            
            if format == "xml":                
                rec = self.parseXml(fpath) 
                
            if format == "json":        
                rec = self.parseJson(fpath) 
                
        return rec
    
    def getremote( self, eg ):
        #print("EntrezGene: get report")
        url = self._url.replace('%%ACC%%',eg)
        #print(url)

        rec = {}

        with open( self.getfpath( eg ), "w" ) as lf:
            for ln in urlopen(url):
                lf.write(ln.decode())
            
        
        # parse xml

        rec = self.parseJson( self.getfpath( eg ) )
        
        return rec

    def getRecord( self, eg, debug=False, delay=1 ):

        rec = self.getlocal( eg, format="json", debug=debug )
        if debug:
            print("rec.json:", rec)
        if rec is None:
            rec = self.getlocal( eg, format="xml",debug=debug )
        if debug:
            print("rec.xml:", rec)
        if rec is None:    
            #rec = self.getremote( eg )
            #sleep(delay)
            pass
        return rec
        
    def parseXml(self, filename, ver="eg001", debug=False):
        res =  super().parseXml( filename, ver=ver )
        return res

    def parseJson(self, filename, ver="eg001", debug=False):
        res =  {}  #super().parseXml( filename, ver=ver )

        jfile = open( filename )
        res = json.load(jfile)

        #print("INPUT")
        #print(json.dumps(res["results"],indent=3))
        #print("INPUT: END\n----------\n")
        
        rec = [ ]
                
        for r in res["results"]:   # r: record (domain)
            #print(r)
            #print()
            #print(r["metadata"].keys())
            meta = r["metadata"]

            cfeature = {'ns':'interpro',
                        'ac': meta['accession'],
                        'name': meta['name'],
                        'alias':[],
                        'source': meta["source_database"],
                        'type': meta["type"],
                        'xref':[]}                
            
            for mb in meta['member_databases']:
                #print("MB",mb, meta['member_databases'][mb])
                for k in meta['member_databases'][mb]:
                    #print("MB  ",k, meta['member_databases'][mb][k])
                    cfeature['xref'].append({'ns':mb, 'ac':k})
                    cfeature["alias"].append(meta['member_databases'][mb][k])
                    
            for p in r["proteins"]:  # proteins listed for current domain               

                # current protein
                cprot = { "ns":"upr",
                          "ac":p['accession'].upper(),
                          "taxon":p['organism'],
                          "feature":[] }
                
                nprot = True
                for cr in rec:                    
                    if cr["ac"] == cprot["ac"]:
                        nprot = False
                        cprot = cr
                        
                if nprot:
                    rec.append( cprot )

                flst = p['entry_protein_locations']

                crange = []
                for crlst in flst:
                    for cr in crlst['fragments']:
                        crange.append(cr)

                #print("FLST:", flst)
                #print("\nCFTR:", cfeature) 

                nft = {"range":crange}

                for k in cfeature.keys():
                    nft[k] = cfeature[k]
                 
                #print("\n",nft,"\n")
                cprot["feature"].append(nft)
                #print("PROT:", cprot)
                #print("RNGS:", crange)
                
                #for f in flst:
                #    
                #    prot["feature"].append(feature)
                #
                #    range = []
                #    feature["range"] = range
                #    
                #    for f0 in f['fragments']:
                #        range.append(f0)
                #    #print(f['fragments'])

                
                #print("FEATURE:", json.dumps(feature,indent=3))
                #print("-----------\n")    
            #print()


        #print("\noutput")
        #print("\n",json.dumps(rec,indent=3))
            
        return rec

    
