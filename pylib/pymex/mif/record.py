import json
import re
from copy import deepcopy

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
        
        self._stoichiometryConvert( ver )        
        
        return self.toXml( ver )
        
    def _stoichiometryConvert(self, ver):
        
        for e in self.root["entrySet"]["entry"]:
            for i in e["interaction"]:
                for p in i["participant"]:
                    if ver == 'mif254': 
                        # find mif300 stoichiometry
                        stset = False
                        if "stoichiometry" in p:
                            stval = str( p["stoichiometry"]["value"] )
                            stset =True
                        else:
                            stval = None
                            
                        if "stoichiometryRange" in p:
                            stmin = str( p["stoichiometryRange"]["minValue"] )
                            stmax = str( p["stoichiometryRange"]["maxValue"] )
                            stset =True
                        else:
                            stmin = None
                            stmax = None
                       
                        if stset:   
                            # replace/add mif254 stoichiometry
                            if "attribute" not in p:
                                p["attribute"]={}
                            ast = None    
                            for a in p["attribute"]:
                                if ("value" in a and 
                                    a["value"].startswith("Stoichiometry:") ):
                                    ast = a
                            if ast is None:        
                                ast =  {'name': 'comment', 'nameAc': 'MI:0612'}
                                p["attribute"].append(ast)
                                 
                            if stval is not None:        
                                ast["value"] = "Stoichiometry: " + stval
                                                 
                            elif stmin is not None and stmax is not None:
                                strng = stmin + " : " + stmax
                                ast["value"] = "StoichiometryRange: " + strng
                                        
                    elif ver == 'mif300':
                    
                        # find mif254 stoichiometry
                        stval = None
                        stmin = None
                        stmax = None
                        if "attribute" in p:
                            for a in p["attribute"]:                                
                                if ("value" in a and 
                                    a["value"].startswith("Stoichiometry:") 
                                    ):
                                        vcol= a["value"].split(" ")
                                        stval = vcol[1]
                                        p["attribute"].remove( a )
                                        break
                                                                
                                if ("value" in a and 
                                    a["value"].startswith("StoichiometryRange:")
                                    ):
                                        vcol= a["value"].split(" ")
                                        stmin = vcol[1]
                                        stmax = vcol[3]
                                        p["attribute"].remove( a )
                                        break
                                        
                        # replace/add mif300 stoichiometry 
                        if stval is not None:  
                            st = p.setdefault("stoichiometry",{})
                            st["value"] =str( stval )
                            
                        else:
                            pass
                            #p.pop("stoichiometry", None)
                            
                        if stmin is not None and stmax is not None:
                            st["minValue"] = str(stmin)                            
                            st["maxValue"] = str(stmax)
                        else:
                            pass
                            #p.pop("stoichiometryRange", None)
                            
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
    def abstIinteractions( self ):
        ret = []        
        for i in range( 0, len( self._entry["abstInteraction" ]) ):        
            ret.append( AbstInteraction( self._entry, n=i ) )        
        return ret
    
    @property    
    def abstInteractionCount( self ):
        return len( self._entry[ "abstInteraction" ] )
    
    def getAbstInteraction( self, n ):
        return AbstInteraction( self._entry , n )
    
    
    @property
    def source(self):
        return Source(self._entry["source"])


class Xref():
    """Xref representation."""
    def __init__( self ):        
        pass
    
    def __len__(self):
        if self._xref is None:
            return 0
        if "secondaryRef" in  self._xref:
            return 1 + len(self._xref["secondaryRef"])
        return 1
        
    @property
    def primaryRef(self):
        if self._xref is None:
            return None
        return Reference( self._xref["primaryRef"] )
    
    @property
    def secondaryRef(self):

        if self._xref is None:
            return None
        ret =[]
        
        if "secondaryRef" not in self._xref:
            return ret                
        
        for sr in self._xref["secondaryRef"]:
            ret.append( Reference(sr) )
        return ret
    
    @property
    def xrefs(self):
        if self._xref is None:
            return None
        ret = []
        ret.append( Reference(self._xref["primaryRef"]) )
        
        if  "secondaryRef" in self._xref:
            for sr in self._xref["secondaryRef"]:
                ret.append( Reference( sr ) )
        return ret
    
    @property
    def xrefCount(self):
        if self._xref is None:
            return 0
        if "secondaryRef" in self._xref:
            return 1 + len(self._xref["secondaryRef"])
        else:       
            return 1
             
class Interaction(Names, Xref):
    """MIF Interaction representation."""
    
    physical = {"names": {
                 "shortLabel": "physical association",
                 "fullName": "physical association"
                 },
              "xref": {
                  "primaryRef": {
                     "db": "psi-mi",
                     "dbAc": "MI:0488",
                     "id": "MI:0915",
                     "refType": "identity",
                     "refTypeAc": "MI:0356"
                     } 
                 }
             } 
         
    direct = {"names": {
                 "shortLabel": "direct interaction",
                 "fullName": "direct interaction"
                 },
              "xref": {
                  "primaryRef": {
                     "db": "psi-mi",
                     "dbAc": "MI:0488",
                     "id": "MI:0407",
                     "refType": "identity",
                     "refTypeAc": "MI:0356"
                     } 
                 }
             }           
            
    
    def __init__( self, entry, n, interaction=None ): 
        self._entry = entry
        if n is not None:
            self._interaction = entry[ "interaction" ][ n ]
        else:
            self._interaction = interaction
            
        self._source = entry[ "source" ]
        self._experiment =  self._interaction["experiment"]
        self._participant = self._interaction["participant"]

        self._names = None
        if "names" in self._interaction:
            self._names = self._interaction["names"]

        self._xref = None
        if "xref" in self._interaction:
            self._xref = self._interaction["xref"]
                
    def expand(self, mode="spoke"):
        """Returns a list of binary interactions generated by expansion
        of multi-molecular interaction according to spoke or marix model.""" 
        
        ret = []
      
        if len(self._participant) <=2:
                return ret
      
        bait = []
        prey = []
        part = []
        
        assType = False
        phyType = False
        dirType = False
        
        if "interactionType" in self._interaction:
            for it in self._interaction["interactionType"]:
                if it["names"]["shortLabel"]=="association":
                    assType = True
                if it["names"]["shortLabel"]=="physical association":
                    phyType = True
                if it["names"]["shortLabel"]=="direct interaction":
                    dirType = True   
                    
        for p in self._participant:
            skip = False
            if "experimentalRole" in p:
                for r in p["experimentalRole"]:
                    if r["names"]["shortLabel"] == "bait":
                        bait.append(p)
                    if r["names"]["shortLabel"] == "prey":
                        prey.append(p)
                    if r["names"]["shortLabel"] == "ancillary":
                        skip = True
            else:
                skip = True 
            if not skip:            
                part.append(p)            
                
        if assType and mode == "spoke":
            for p1 in bait:
                for p2 in prey:
                                      
                    binary = {}
                    for k in self._interaction.keys():
                        if k not in ["participant","interactionType"]:
                            binary[k] = self._interaction[k]
                  
                    itype = deepcopy( self.physical )
                    binary.setdefault("interactionType",[]).append( itype )
                    bprt =  binary.setdefault("participant",[])
                    bprt.append(p1)
                    bprt.append(p2)
                    
                    ret.append( Interaction( self._entry, None, binary ) )
                    
        if (phyType or dirType) and mode == "matrix":           
            for i in range(0,len(part)):
                for j in range(i+1,len(part)):
                    binary = {}
                        
                    for k in self._interaction.keys():
                        if k not in ["participant","interactionType"]:
                            binary[k] = self._interaction[k]

                    if  dirType:                
                        itype = deepcopy( self.direct )
                    else:
                        itype = deepcopy( self.physical )
                    binary.setdefault("interactionType",[]).append( itype )
                    bprt =  binary.setdefault("participant",[])
                    bprt.append(part[i])
                    bprt.append(part[j])
                    
                    ret.append( Interaction( self._entry, None, binary ) )
                    
        return ret
        
    @property
    def imexid(self):
        if "imexId" in self._interaction:
            return self._interaction["imexId"]
        return None
    
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
    def availability(self):
        if "availability" in self._interaction:
            return self._interaction["availability"]["value"]
        return None
    
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
       
    @property
    def confidence(self):
        if "confidence" in  self._interaction:
            return bool(self._interaction["confidence"])
    
    @property
    def modelled(self):
        if "modelled" in  self._interaction:
            return bool(self._interaction["modelled"])
        return False

    @property
    def intramolecular(self):
        if "intramolecular" in  self._interaction:
            return bool(self._interaction["intramolecular"])
        return False
    
    @property
    def negative(self):
        if "negative" in  self._interaction:
            return bool(self._interaction["negative"])
        return False
    

class AbstInteraction(Names, Xref):
    """MIF AbstractInteraction representation."""
    def __init__( self, entry, n ):    
        self._entry = entry
        self._interaction = entry[ "abstractInteraction" ][ n ]
        self._source = entry[ "source" ]       
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
            if isinstance(self._interaction["interactionType"], dict):            
                return CvTerm(self._interaction[ "interactionType" ])
        return None

    @property
    def interactorType(self):
        if "interactorType" in self._interaction:            
            if isinstance(self._interaction["interactorType"], dict):            
                return CvTerm(self._interaction[ "interactorType" ])
        return None
    
    @property
    def evidenceType(self):
        if "evidenceType" in self._interaction:            
            if isinstance(self._interaction["evidenceType"], dict):            
                return CvTerm(self._interaction[ "evidenceType" ])
        return None

    @property
    def organism(self):
        if "organism" in self._interaction:                                  
            return Host( self._interaction["organism"] )
        return None 

    @property
    def source(self):
        return Source( self._source )

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
        self._interactor = self._participant["interactor"]
        self._interaction = interaction
        
        if "names" in  self._participant:            
            self._names = self._participant["names"]
        else:
            self._names = self._interactor["names"]
        
        if "xref" in  self._participant:
            self._xref = self._participant["xref"]
            
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
    def stoich(self):        
        #mif300 style: fixed value
        if "stoichiometry" in self._participant:
             sval = self._participant["stoichiometry"]
             try:                        
                 valb = float(sval)
                 vale = float(sval)
                 return (valb,vale)
             except:
                 return (str(sval),str(sval))
        #mif300 style: range
        if "stoichiometryRange" in self._participant:
             try:
                svalb = self._participant["stoichiometryRange"]["minValue"]
                svale = self._participant["stoichiometryRange"]["maxValue"]
                                                      
                return (float(svalb),float(svale))
             except:
                return (str(svalb),str(svale))             
            
        # mif254 style
        if "attribute" in self._participant:
            for a in self._participant["attribute"]:
                if "value" in a:
                    match = re.match('Stoichiometry: (.+)',a["value"])
                    if match:
                        sval = match.group(1)
                        try:                        
                            valb = float(sval)
                            vale = float(sval)
                            return (valb,vale)
                        except:
                            return (str(sval),str(sval))
                        
                    match = re.match('StoichiometryRange: (.+)',a["value"])
                    if match:
                        svalc = match.group(1).split(":")
                        try:                        
                            valb = float(svalc[0])
                            vale = float(svalc[1])
                            return (valb,vale)
                        except:
                            return (str(sval),str(sval))    
                                                
        return (0.0, 0.0)            
    
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
        self._range =  feature["featureRange"]       
        
        self._meth = None
        if "featureDetectionMethod" in feature:
            self._meth = feature["featureDetectionMethod"]

        if "attribute" in feature:
            self._attr = feature["attribute"]

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
        ret = []
        for r in self._range:
            ret.append( Range(r) )
        return ret
    
    @property
    def attribs(self):    
        if self._attr is None:
            return None
        return Attribs( self._attr )


class Range():
    def __init__(self, rng):
        self._rng = rng    

    @property
    def begStat(self):
        return CvTerm(self._rng["beginStatus"])

    @property
    def begPosition(self):
        if "begin" in self._rng:
            if "value" in self._rng["begin"]:
                pos = self._rng["begin"]["value"]
                return (int(pos),int(pos))
            if ("begin" in self._rng["begin"]  and 
                        "end" in self._rng["begin"]):
                posb = self._rng["begin"]["begin"]
                pose = self._rng["begin"]["end"]
                return ( int(posb) , int(pose) )    
        return None
       
    @property
    def endStat(self):
        return CvTerm(self._rng["endStatus"])

    @property
    def endPosition(self):
        if "begin" in self._rng:
            if "value" in self._rng["begin"]:
                pos = self._rng["begin"]["value"]
                return ( int(pos), int(pos) )
            if ("begin" in self._rng["begin"]  and 
                "end" in self._rng["begin"]):
                posb = self._rng["begin"]["begin"]
                pose = self._rng["begin"]["end"] 
                return ( int(posb), int(pose) )    
        return None
       
 
class Availability():
    """MIF Availability representation."""
    def __init__( self, avail ):
        self._avail = avail

    def __repr__(self):
        return str(self._avail)

        
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





