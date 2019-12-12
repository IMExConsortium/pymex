import copy
import json
import psimi
from lxml import etree as ET

class Interactor(psimi.Base):
    """The reference version of a biomolecule. Corresponds to 
       <interactor>...</interactor> element in the PSM-MI XML records.
    """
    def __init__( self, i10r=None, root=None ):
        super(Interactor, self ).__init__( raw = i10r, root = root)
 
    def __str__( self ):
        rep=[]
        rep.append( "  Interactor:")
        rep.append( "   Label: " + self.label )
        rep.append( "   Name: " + self.name )
        rep.append( "   Type: " + str(self.type) )
        rep.append( "   Species: " + str(self.species) )
        rep.append( "   PXref: " + str(self.pxref) )
        rep.append( "   SXref: " + str(self.sxref) )
        return '\n'.join(rep)

    def __repr__( self ):
        rep={}
        rep['label']=self.label
        rep['name']=self.name
        rep['type']=self.type
        rep['species']=self.species
        rep['pxref']=self.pxref
        rep['sxref']=self.sxref
        
        return json.dumps(rep,sort_keys=True, indent=4)
      
    @property
    def species( self ):
        """Native species the biomolecule is made in (if present)."""
        if 'species' in self._raw:
            return self._raw['species']
        else:
            return None
        
    @property
    def type( self ):
        """Molecule type.
        """
        return self._raw['type']
    
    @property
    def sequence( self ):
        """Biopolymer sequence.
        """
        if 'sequence' in self._raw.keys():
            return self._raw['sequence']
        else:
            return None
