
#from lxml import etree as ET
import json
#import os

from pymex import mif

class Record(mif.XmlRecord):
    """MIF record representation. Inherits XML parsing and serialization from XmlRecord"""
    
    def __init__(self, root=None):

        super().__init__(root)
        
        self.NAMESPACES = { "mif254":"http://psi.hupo.org/mi/mif",
                            "mif300":"http://psi.hupo.org/mi/mif300"}
        self.LEN_NAMESPACE = {"mif254":28, "mif300":31}
        self.MIFNS = { "mif254":{None:"http://psi.hupo.org/mi/mif",
                                 "xsi":"http://www.w3.org/2001/XMLSchema-instance"},
                       "mif300":{None:"http://psi.hupo.org/mi/mif300",
                                 "xsi":"http://www.w3.org/2001/XMLSchema-instance"}}
        
        self.PARSEDEF={"mif254":"defParse254.json",
                       "mif300":"defParse300.json"}
        
        self.MIFDEF= {"mif254":"defMif254.json",
                      "mif300":"defMif300.json"}
        
    def parseMif(self, filename, ver="mif254", debug=False):
        return self.parseXml( filename, ver=ver )
   
    def toMif( self, ver='mif254' ):
        """Builds MIF elementTree from a Record object."""
        return self.toXml( ver )
        
    @property
    def entry(self):
        """Returns the first (default) entry of the record"""
        
        return Entry( self.root['entrySet']['entry'][0] )
    
    @property
    def entryCount(self):
        return len( self.root['entrySet']['entry'])
    
    def getEntry( self, n = 0 ):
        "Returns i-th entry of the record."""
        if n < len( self.root['entrySet']['entry'] ):
            return Entry( self.root['entrySet']['entry'][n] )
        else:
            return None
    
    @property          
    def interactions(self):
        """Returns interactions of the first (default) entry of the record."""                        
        return Entry( self.root['entrySet']['entry'][0] ).interactions
    
    @property
    def interactionCount(self):
        return len( self.root['entrySet']['entry'][0]["interaction"]) 
    
    def getInteraction( self, n ):
        return Interaction( self.root['entrySet']['entry'][0], n )
    
       
class Alias():

    def __init__(self, alias ):
        self._alias = alias
    
    def __repr__(self):
        return json.dumps(self._alias)

    def __str__(self):
        return str(self._alias["value"])

    @property
    def type(self):
        if "type" in self._alias:
            return self._alias["type"]
        return None
    
    @property
    def typeAc(self):
        if "typeAc" in self._alias:
            return self._alias["typeAc"] 
        return None


class Names():
    
    def __init__(self):
        pass
    
    def __repr__(self):
        return json.dumps(self._names)
    
    @property
    def label(self):
        return self._names["shortLabel"]
            
    @property
    def name(self):
        return self._names["fullName"]
    
    @property
    def alias(self):
        ret = []
        if "alias" in self._names:
            for a in self._names["alias"]:
                ret.append( Alias( a ) )
        return ret    
    
    
class Entry():
    """MIF Entry representation."""
    def __init__( self, entry ):        
        self._entry = entry    
    
    @property
    def interactions( self ):
        ret = []        
        for i in range( 0, len( self._entry["interaction" ]) ):        
            ret.append( Interaction( self._entry, n=i ) )        
        return ret
    
    @property    
    def interactionCount( self ):
        return len( self._entry[ "interaction" ] )
    
    def getInteraction( self, n ):
        return Interaction( self._entry , n )
     
    @property
    def source(self):
        return Source(self._entry["source"])


class Xref():
    """Xref representation."""
    def __init__( self ):        
        pass
    
    def __len__(self):
        if "secondaryRef" in  self._xref:
            return 1 + len(self._xref["secondaryRef"])
        return 1
        
    @property
    def primaryRef(self):   
        return Reference( self._xref["primaryRef"] )
    
    @property
    def secondaryRef(self):
        ret =[]

        if "secondaryRef" not in self._xref:
            return ret                
        
        for sr in self._xref["secondaryRef"]:
            ret.append( Reference(sr) )
        return ret
    
    @property
    def xrefs(self):
        ret = []
        ret.append( Reference(self._xref["primaryRef"]) )
        
        if  "secondaryRef" in self._xref:
            for sr in self._xref["secondaryRef"]:
                ret.append( Reference( sr ) )
        return ret
    
    @property
    def xrefCount(self):
        return 1 + len(self._xref["secondaryRef"])
    
            
class Interaction(Names, Xref):
    """MIF Interaction representation."""
    def __init__( self, entry, n ):    
        self._entry = entry
        self._interaction = entry[ "interaction" ][ n ]
        self._source = entry[ "source" ]
        self._experiment =  self._interaction["experiment"]
        self._participant = self._interaction["participant"]

        self._names = None
        if "names" in self._interaction:
            self._names = self._interaction["names"]

        self._xref = None
        if "xref" in self._interaction:
            self._xref = self._interaction["xref"]
        
    @property
    def participants(self):
        ret = []        
        for i in self._participant: 
            ret.append( Participant( i,  self._interaction ) )        
        return ret
        
    @property 
    def participantCount(self): 
        return len( self._participant )

    def getParticipant( self, n = 0 ):
        if n < len( self._participant ):            
            return Participant( self._participant[ n ] ) 
        else:    
            return None
        
    @property
    def type(self):
        if "interactionType" in self._interaction:
            if isinstance(self._interaction["interactionType"], list):            
                return CvTerm(self._interaction[ "interactionType" ][0])
            if isinstance(self._interaction["interactionType"], dict):            
                return CvTerm(self._interaction[ "interactionType" ])
        return None
    
    @property
    def types(self):
        if "interactionType" in self._interaction:
            if isinstance(self._interaction["interactionType"], list):
                ret = []
                for t in self._interaction["interactionType"]:
                    ret.append( CvTerm(t) )
                return ret
        return None

    @property
    def source(self):
        return Source( self._source )

    @property
    def experiments(self):
        ret = []
        for i in self._experiment:
            ret.append( Experiment( self._experiment[i] ) )
        return ret
        
    @property 
    def experimentCount(self): 
        return len( self._experiment )
  
    
    @property
    def experiment(self):
        if len( self._experiment ) == 1:
            return Experiment( self._experiment[0] )
        else:
            return None
    
    def getExperiment( self, n = 0 ):
        if n < len( self._experiment ):            
            return Experiment( self._experiment[ n ] ) 
        else:    
            return None
                
    @property
    def attribs(self):    
        if self._attr is None:
            return None
        return Attribs( self._attr )

    @property
    def params(self):    
        if self._param is None:
            return None
        return Params( self._param )
       

class Reference():
    def __init__(self, xref):
        self._xref = xref
           
    def __repr__(self):
        return json.dumps( self._xref )
        
    @property
    def db(self):
        if "db" in self._xref:
            return self._xref["db"]
        return None
    
    @property
    def dbAc(self):
        if "dbAc" in self._xref:
            return self._xref["dbAc"]
        return None

    @property
    def ac(self):
        if "ac" in self._xref:
            return self._xref["ac"]
        return None
    
    @property
    def version(self):
        if "version" in self._xref:
            return self._xref["version"]
        return None
    
    @property
    def refType(self):
        if "refType" in self._xref:
            return self._xref["refType"]
        return None
    
    @property
    def refTypeAc(self):
        if "refTypeAc" in self._xref:
            return self._xref["refTypeAc"]
        return None



class Attribute():
    """MIF Attribute representation."""
    def __init__(self,attr):    
        self._attr = attr

    def __repr__(self):
        return json.dumps(self._attr)

    @property
    def name(self):
        if "name" in self._attr:
            return str(self._attr["name"])
        return None
    
    @property        
    def nameAc(self):
        if "nameAc" in self._attr:
            return str(self._attr["nameAc"])
        return None
     
    @property        
    def value(self):
        if "value" in self._attr:
            return str(self._attr["value"])
        return None
      
class Attribs():   
    def __init__(self, attribs):
        self._attribs = attribs
        
    def __getitem__(self, pos):    
        return Attribute( self._attribs[pos] )
   
    def __len__(self):
        return len(self._attribs)
    
    
class Parameter():
    """MIF Parameter representation."""
    def __init__(self, param):    
        self._param = param

    @property
    def term(self):
        return str(self._param["term"])

    @property
    def termAc(self):
        if "termAc" in self._param:
            return str(self._param["termAc"])
        return None
        
    @property
    def unit(self):
        if "unit" in self._param:
            return str(self._param["unit"])
        return None
    
    @property
    def unitAc(self):
        if "termAc" in self._param:
            return str(self._param["termAc"])
        return None

    @property
    def value(self):
        base = 10.0
        exp = 0.0
        factor = float(self._param["factor"])

        if "base" in self._param:
            base = float(self._param["base"])
        if "exponent" in self._param:
            exp = float(self._param["exponent"])   

        return factor * pow( base, exp)
            
    @property
    def uncertainty(self):
        if "uncertainty" in self._param:
            return float(self._param["uncertainty"])
        else:
            return float(0.0)
        
    @property
    def error(self):
        if "uncertainty" in self._param:
            return float(self._param["uncertainty"])
        else:
            return float(0.0)


class Params():    
    def __init__(self, params):
        self._params =  params
        
    def __getitem__(self, pos):    
        return Parameter( self._params[pos] )
   
    def __len__(self):
        return len(self._params)
    
    
class Source( Names, Xref ):
    """MIF Source representation."""   
    def __init__( self, source ):    
        self._source = source
        self._names = source["names"]
        self._xref = source["xref"]

    
class Participant( Names,Xref ):
    """MIF Participant representation."""
    def __init__(self, participant, interaction ):    
        self._participant = participant
        self._interaction = interaction
        self._names = self._participant["names"]
        self._xref = self._participant["xref"]
        self._interactor = self._participant["interactor"]
            
        if "hostOrganism" in self._participant:
            self._host = self._participant["hostOrganism"]
        else:
            self._host =  [ self._interactor["organism"] ]
            
        self._meth = None
        if "participantIdentificationMethod" in participant:
            self._meth = participant["participantIdentificationMethod"]
        else:
            if ("experiment" in interaction and 
                len(interaction["experiment"]) == 1):       
                ex = interaction["experiment"][0]
                if "participantIdentificationMethod" in ex:
                    self._meth =  ex["participantIdentificationMethod"]
            
        self._biorole = None
        if "biologicalRole" in participant:     
            if isinstance( participant["biologicalRole"], dict ):
                self._biorole = [participant["biologicalRole"]]
            elif isinstance( participant["biologicalRole"], list ):   
                self._biorole = participant["biologicalRole"]
                
        self._exprole = None
        if "experimentalRole" in participant:     
            if isinstance( participant["experimentalRole"], list ):
                self._exprole = participant["experimentalRole"]
            elif isinstance( participant["experimentalRole"], dict ):   
                self._exprole = [participant["experimentalRole"]]
             
        self._feature = None        
        if "feature" in self._participant:
            self._feature = self._participant["feature"]
                
        self._confidence = None   
        if "confidence" in self._participant:
            self._confidence =self._participant["confidence"]
        
        self._parameter = None 
        if "parameter" in self._participant:
            self._parameter = self._participant["confidence"]
         
        self._attribute = None 
        if "attribute" in self._participant:
            self._attribute = self._participant["attribute"]
            
    @property
    def interactor( self ):       
        return Interactor( self._interactor )
   
    @property
    def hosts( self ):
        ret = []
        for h in self._host: 
            ret.append( Host( h ) )        
        return ret
    
    @property
    def host( self ):
           if len( self._host ) == 1:
               return Host( self._host[0] )
           else:
               return None

    @property
    def meth( self ):
        if self._meth is not None:
            ret = []
            for m in self._meth:
                ret.append( CvTerm( m ) )
            return ret    
        return None

    @property
    def features( self ):
        ret = []
        for f in self._feature:
            ret.append( Feature( f ) )
            
        return ret
    
    @property
    def confidence( self ):
        if self._confidence is not None:
            return list(self._confidence)
    
    
class Experiment():
    """MIF Experiment representation."""
    def __init__( self, experiment ):    
        self._experiment = experiment


class Interactor(Names, Xref):
    """MIF Interactor representation."""
    def __init__( self, interactor ):
        self._interactor = interactor
        self._names = interactor["names"]
        self._xref = interactor["xref"]


class Feature(Names, Xref):
    """MIF Feature representation."""
    def __init__( self, feature ):    
        self._feature = feature
        self._names= feature["names"]
        self._xref = feature["xref"]
        
        self._meth = None
        if "featureDetectionMethod" in feature:
            self._meth = feature["featureDetectionMethod"]
        
    @property
    def type(self):
        return CvTerm(self._feature["featureType"])

    @property
    def meth( self ):
        if self._meth is not None:
            ret = []
            for m in self._meth:
                ret.append( CvTerm( m ) )
            return ret    
        return None
    
    @property
    def range(self):
        pass
    
    @property
    def attrib(self):
        pass
   
    
                
class Availability():
    """MIF Availability representation."""
    def __init__( self, avail ):
        self._avail = avail

        
class CvTerm( Names, Xref ):
    """Mif CvTerm representation."""
    def __init__(self, cvterm):
        print(type(cvterm))
        self._cvterm = cvterm
        self._names = cvterm["names"]
        self._xref = cvterm["xref"]

    def __repr__(self):
        return json.dumps(self._cvterm)


class Host( Names ):
    """MIF Host representation. Optional cell line/compartment/tissue information."""
    def __init__(self, host):
        self._host = host
        self._names = host["names"]
        
    def __repr__(self):
        return json.dumps(self._host)

    @property
    def taxid(self):
        return str(self._host["ncbiTaxId"])
    
    @property
    def cellType(self):
        if "cellType" in self._host:
            return CvTerm(self._host["cellType"])
        return None

    @property
    def compartment(self):
        if "compartment" in self._host:
            return CvTerm(self._host["compartment"])
        return None

    @property
    def tissue(self):
        if "tissue" in self._host:
            return CvTerm(self._host["tissue"])
        return None






