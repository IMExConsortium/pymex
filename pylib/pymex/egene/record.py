import os

from urllib.request import urlopen
from time import sleep
import pymex


class Record( pymex.xmlrecord.XmlRecord ):
 
    def __init__( self, root=None, mode='dev', debug=False ):

        myDir = os.path.dirname( os.path.realpath(__file__))
        self.uniConfig = { "eg001": {"IN": os.path.join( myDir, "defEGParse001.json"),
                                      "OUT": os.path.join( myDir, "defEGXml001.json" ) }
        }
            
        super().__init__(root, config=self.uniConfig,
                         postproc = { "strand":self._strand })
        
        self.mode = mode
        self._debug = debug    

        self._mirror = '/mnt/mirrors/entrezgene/records'
        self._url = 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=gene&id=%%ACC%%&retmode=xml'
            
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
                         

    def getfpath( self, eg ):

        cdir = self._mirror
        eg = "0"*12+ str(eg)
        eg = eg[-12:]
        for i in range(0,9,3):
            cdir +=  "/" +eg[i:i+3]
            if not os.path.isdir(cdir):
                os.mkdir(cdir) 

        fpath = cdir + "/" + eg + ".xml"
        return fpath

            
    def getlocal( self, eg ):

        rec = None

        fpath = self.getfpath( eg )
                
        if os.path.isfile( fpath ):
            
            # parse xml

            rec = self.parseXml( fpath ) 
            
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

        rec = self.parseXml( self.getfpath( eg ) )
        
        return rec

    def getRecord( self, eg, debug=False, delay=1 ):

        rec = self.getlocal( eg )
        
        if rec is None:
            rec = self.getremote( eg )
            sleep(delay)
        return rec
        
    def parseXml(self, filename, ver="eg001", debug=False):
        res =  super().parseXml( filename, ver=ver )
        return res

    
