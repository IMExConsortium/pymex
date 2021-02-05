# -*- coding: utf-8 -*-
"""
Created on Wed Aug 19 02:05:33 2020

@author: andrei
"""

import json
import re

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
             
class Bibref(Xref):
    def __init__( self, xref, attr ):
        self._xref = xref
        self._attribute = attr
                
    @property
    def attribs(self):    
        if self._attribute is None:
            return None
        return Attribs( self._attribute )
    
    
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
        if "id" in self._xref:
            return self._xref["id"]

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
        
        self._xref = source["xref"] if "xref" in  source else None
        self._bibref = source["bibref"] if "bibref" in  source else None
        self._attribute = source["attribute"] if "attribute" in  source else None
                  

    @property
    def releasedate(self):
        if "releaseDate" in self._source:
            return str(self._source["releaseDate"])
        return None
            
    @property
    def bibref(self):    
        if self._bibref is not None:                           
            xref = self._bibref["xref"] if "xref" in self._bibref else None
            attr = self._bibref["attribute"] if "attribute" in self._bibref else None                 
            return Bibref( xref, attr )
        return None
    
    @property
    def attribs(self):    
        if self._attribute is not None:        
            return Attribs( self._attribute )
        return None
    
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
                
        self._xref = self._participant["xref"] if "xref" in self._participant else None
            
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
             
        self._feature = self._participant["feature"] if "feature" in self._participant else None 
        self._confidence =self._participant["confidence"] if "confidence" in self._participant else None 
        self._parameter = self._participant["parameter"] if "parameter" in self._participant else None         
        self._attribute = self._participant["attribute"] if "attribute" in self._participant else None
            
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
    
    
class Experiment(Names, Xref):
    """MIF Experiment representation."""
    def __init__( self, experiment ):    
        self._experiment = experiment
                 
        self._names = self._experiment["names"] if "names" in self._experiment else None
        self._xref = self._experiment["xref"] if "xref" in self._experiment else None
        self._bibref = self._experiment["bibref"] if "bibref" in self._experiment else None
        self._attribute = self._experiment["attribute"] if "attribute" in self._experiment else None
          
        if "hostOrganism" in self._experiment:
            self._host = self._experiment["hostOrganism"]
        else:
            self._host = None
            
        self._meth = None
        if "interactionDetectionMethod" in self._experiment:
            self._meth = self._experiment["interactionDetectionMethod"]
       
        self._pmeth = None
        if "participantIdentificationMethod" in self._experiment:
            self._meth = self._experiment["participantIdentificationMethod"]

        self._fmeth = None
        if "featureIdentificationMethod" in self._experiment:
            self._fmeth = self._experiment["featureIdentificationMethod"]

    @property 
    def bibref(self):
        if self._bibref is not None:
            xref = self._bibref["xref"] if "xref" in self._bibref else None
            attr = self._bibref["attribute"] if "attribute" in self._bibref else None
                                         
            return Bibref( xref, attr )            
        return None
    
    @property
    def hosts( self ):
        if self._host is None:
            return None
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
    def method(self):
        if self._meth is not None:
            return CvTerm( self._meth )    
        return None
    
    @property       
    def partmethod(self):
        if self._pmeth is not None:
            return CvTerm( self._pmeth )
        return None
    
    @property        
    def featmethod(self):
        if self._fmeth is not None:
            return CvTerm( self._fmeth )        
        return None
    
    @property        
    def confidence(self):
        if self._conf is not  None:
            ret = []
            for c in self._conf:
                ret.append( Confidence( c ) )
            return ret 
        return None
        
    @property
    def attribs(self):    
        if self._attribute is not None:
            return Attribs( self._attribute )
        return None

class Interactor(Names, Xref):
    """MIF Interactor representation."""
    def __init__( self, interactor ):
        self._interactor = interactor
        self._names = interactor["names"]
        self._xref = interactor["xref"]
        self._type = interactor["interactorType"]
        self._host = interactor["organism"]
        
        self._sequence = None
        if "sequence" in interactor:
            self._sequence = interactor["sequence"]

    @property
    def type( self ):        
        return CvTerm(self._type)      

    @property
    def host( self ):        
        return Host( self._host )
    
    @property
    def sequence( self ):        
        return self._sequence
      

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
            self._attribute = feature["attribute"]

    @property
    def type(self):
        return CvTerm(self._feature["featureType"])

    @property
    def methods( self ):
        if self._meth is not None:
            ret = []
            for m in self._meth:
                ret.append( CvTerm( m ) )
            return ret    
        return None
      
    
    @property
    def ranges(self):         
        ret = []
        for r in self._range:
            ret.append( Range(r) )
        return ret
    
    @property
    def attribs(self):    
        if self._attribute is not None:
            return Attribs( self._attribute )
        return None

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

class Confidence:
    """MIF Confidence representation. """
    def __init__(self, conf):
        self._conf = conf

    @property
    def unit(self):
        return CvTerm(self._conf["unit"])

    @property
    def value(self):
        return str(self._conf["value"])
    
