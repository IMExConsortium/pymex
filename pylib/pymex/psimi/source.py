import copy
import json
import psimi

from lxml import etree as ET

class Source(psimi.Base):
    """The source of the database record.
    """
    def __init__( self, src = None, root = None):    
       super(Source, self).__init__( raw = src, root = root) 
        
    def __repr__(self):        
        rep=[]        
        rep.append(" Source:")
        rep.append( "  Label:\t" + self.label )
        rep.append( "  Name:\t" + self.name )
        rep.append( "  PXref\t:" + str(self.pxref) )
        rep.append( "  SXref\t:" + str(self.sxref) )
        rep.append('')
        return '\n'.join( rep )

    @property
    def src(self):
        """Raw source record data structure.   
        """
        return self._raw
    
    @property    
    def bibref( self ):
        """A reference to the bibliographic information about the
        source of the interaction record (most commonly a database)
        """
        if 'bibref' in self._raw.keys():
            return self._raw['bibref']
        return None

    @property    
    def attlst( self ):
        """Atrribute list.
        """
        if 'attList' in self._raw.keys():
            return self._raw['attList']
        return None
