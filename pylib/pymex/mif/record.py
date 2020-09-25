# -*- coding: utf-8 -*-
"""
Created on Wed Aug 19 02:05:33 2020

@author: andrei
"""

import os
import pymex
from pymex import xmlrecord, mif

class Record(xmlrecord.XmlRecord):
    """MIF record representation. Inherits XML parsing and serialization from xml.XmlRecord"""
    
    def __init__(self, root=None):

        myDir = os.path.dirname( os.path.realpath(__file__))
        self.mifConfig = { "mif254": {"IN": os.path.join( myDir, "defParse254.json"),
                                      "OUT": os.path.join( myDir, "defMif254.json" )},
                           "mif300": {"IN": os.path.join( myDir, "defParse300.json"),
                                      "OUT": os.path.join( myDir, "defMif300.json" )}}
        
        super().__init__(root, config=self.mifConfig )
                
    def parseMif(self, filename, ver="mif254", debug=False):
        return self.parseXml( filename, ver=ver )
   
    def toMif( self, ver='mif254' ):
        """Builds MIF elementTree from a Record object."""
        
        self._stoichiometryConvert( ver )        
        
        return self.toXml( ver, "entrySet", "ExpandedEntrySet" )
        
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
        return mif.Entry( self.root['entrySet']['entry'][0] )
    
    @property
    def entryCount(self):
        return len( self.root['entrySet']['entry'])
    
    def getEntry( self, n = 0 ):
        "Returns i-th entry of the record."""
        if n < len( self.root['entrySet']['entry'] ):
            return mif.Entry( self.root['entrySet']['entry'][n] )
        else:
            return None
    
    @property          
    def interactions(self):
        """Returns interactions of the first (default) entry of the record."""                        
        return mif.Entry( self.root['entrySet']['entry'][0] ).interactions
    
    @property
    def interactionCount(self):
        return len( self.root['entrySet']['entry'][0]["interaction"]) 
    
    def getInteraction( self, n ):
        return mif.Interaction( self.root['entrySet']['entry'][0], n )
    
       
class Entry():
    """MIF Entry representation."""
    def __init__( self, entry ):        
        self._entry = entry    
    
    @property
    def interactions( self ):
        ret = []        
        for i in range( 0, len( self._entry["interaction" ]) ):        
            ret.append( mif.Interaction( self._entry, n=i ) )        
        return ret
    
    @property    
    def interactionCount( self ):
        return len( self._entry[ "interaction" ] )
    
    def getInteraction( self, n ):
        return mif.Interaction( self._entry , n )
  
    @property
    def abstIinteractions( self ):
        ret = []        
        for i in range( 0, len( self._entry["abstInteraction" ]) ):        
            ret.append( mif.AbstInteraction( self._entry, n=i ) )        
        return ret
    
    @property    
    def abstInteractionCount( self ):
        return len( self._entry[ "abstInteraction" ] )
    
    def getAbstInteraction( self, n ):
        return mif.AbstInteraction( self._entry , n )
    
    
    @property
    def source(self):
        return mif.Source(self._entry["source"])

       








        
        
        
        

