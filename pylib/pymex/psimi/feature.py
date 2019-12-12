import copy
import json
import psimi
from lxml import etree as ET

class Feature(psimi.Base):
    """A feature of the biomolecule that was determined as relevant
    to the exeriment demonstrating the described interaction.
    """
    def __init__( self, ftr = None, root = None):    
        super(Feature, self ).__init__( raw = ftr, root = root)
        
    def __repr__(self):        
        rep=[]
        rep.append(" Feature:")
        rep.append( "  Label:" + str(self.label) )
        rep.append( "  Name:" + str(self.name) )
        rep.append( "  PXref:" + str(self.pxref) )
        rep.append( "  SXref:" + str(self.sxref) )
        return '\n'.join( rep )

    @property    
    def type( self ):
        """Feature type.
        """
        if 'type' in self._raw.keys():
            return self._raw['type']
        return None

    @property    
    def detmth( self ):
        """A list of experiemntal methods used to indentify the feature.
        """
        if 'detmth' in self._raw.keys():
            return self._raw['detmth']
        return None

    @property    
    def rnglst( self ):
        """A list of monomer positions (typically, aminoacids or bases)
        corresponding to the described feature. The numbering uses positions
        defined by the reference state of the participant, as specified
        by the interactor. 
        """
        if 'rnglst' in self._raw.keys():
            return self._raw['rnglst']
        return None

    @property    
    def attlst( self ):
        """Attribute list.
        """
        if 'attlst' in self._raw.keys():
            return self._raw['attlst']
        return None
