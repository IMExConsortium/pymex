import sys
import json

import dxf as DXF 
from lxml import etree as ET

class DXF15Record():
    """  Representation of a single DXF15 dataset file/record.
    """
    def __init__( self, dxf=None, root=None ):
        self.nsp = { 'dxf': 'http://dip.doe-mbi.ucla.edu/services/dxf15' }
        self.nsmap = {None: self.nsp['dxf'] }
        self.dxfp = "{%s}" % self.nsp['dxf']
        
        self._root = root

        if isinstance( dxf, list ):
            self._dxf = dxf
        elif isinstance( dxf, dict ):
            self._dxf = [dxf]
        else:
            raise TypeError
        
        if dxf is None:
            self._ndlst = None
        else:
            self._ndlst = []
            if isinstance( dxf, dict ):
                self._ndlst.append( DXF.DXF15Node( dxf, self._root) )
            elif isinstance( dxf, list ):
                for nd in dxf:
                    self._ndlst.append( DXF.DXF15Node( nd, self._root) )

    @property
    def root( self ):
        return self._root

    @property
    def dom( self ):
        return self._root

    @property
    def dxf( self ):
        return self._dxf

    @property
    def node( self ):
        return self._ndlst
    
    def __str__(self):
        return self.__repr__()
    
    def __repr__(self):        
        rep=[]
        rep.append("Record:")        
        rep.append(" Nodes:")
        if self._ndlst:
            for nd in self._ndlst:    
                rep.append( repr( nd ) )
            
        return '\n'.join(rep)

    def addNode( self, node ):

        if self._dxf is None:
            self._dxf = [] 

        if self._ndlst is None:
            self._ndlst = [] 
        
        if isinstance( node, dippy.DXF15Node ):
            self._ndlst.append( node )            
            self._dxf.append( node.dxf )
            
        else:
            self._ndlst.append( dippy.DXF15Node( node, self._root) )
    
    def dxfstr( self ):
        sdom = ET.Element( self.dxfp + "dataset", nsmap = self.nsmap)
        id = 0
        if self._ndlst:
            for nd in self._ndlst:                
                (self, nid) = nd.dxfdom( parent = sdom, id = id )                 
                id = nid
        return ET.tostring(sdom, encoding='utf-8').decode('utf-8')
        
