import copy
import json
import psimi
from lxml import etree as ET

class Base():
    """The base class of psimi data records. Supports label, 
    name and cross-reference fields, including local, reversible 
    modifications. 
    """
    def __init__( self, raw=None, root=None ):
        self.ns = { 'mif': 'http://psi.hupo.org/mi/mif' }
        self._root = root
        self._raw = raw

        # local modifications
        if self._raw is not None:
            if 'local' not in self._raw.keys():
                self._raw['local'] = {}
    
    @property
    def root ( self ):
        """Top level record data structure."""
        return self._root

    @property
    def raw( self ):
        """Raw instance data structure."""
        return self._raw

    @property
    def mif25(self):
        """Source DOM data structure (if present)"""
        if self._raw['dom'] is not None:
            return str(ET.tostring(self.int['dom']),'utf-8')
        return ''
    
    @property
    def label( self ):
        """Short(er) name (label) of the object. Corresponds to
        <names><shortLabel>...</shortLabel></names> element in
        a PSI-MI XML file
        """
        if self._raw is not None and 'local' in self._raw.keys():
            if 'label' in self._raw['local'].keys():
                if self._raw['local']['label'] is not None:
                    return self._raw['local']['label']
        return self._raw['label']

    def setLabel( self, label=None):
        """Local modification of the object label. Setting it to 
        None reverts the modification.
        """
        if self._raw is not None:
            if 'local' not in self._raw.keys():
                self._raw['local'] = {}
            self._raw['local']['label'] = label

    @property
    def name( self ):
        """Full name/description of the object. Corresponds to
        <names><fullName>...</fullName></names> element in 
        a PSI-MI XML file
        """
        if self._raw is not None and 'local' in self._raw.keys():
            if 'name' in self._raw['local'].keys():
                if self._raw['local']['name'] is not None:
                    return self._raw['local']['name']
        return self._raw['name']

    def setName( self, name):
        """Local modification of the object name. Setting it to 
        None reverts the modification.
        """
        if self._raw is not None:
            if 'local' not in self._raw.keys():
                self._raw['local'] = {}
            self._raw['local']['name'] = name
                
    @property
    def pxref( self ):
        """Primary cross-reference of the object.  Corresponds to
        <xref><primaryRef/></xref> element in a PSI-MI XML file.
        """
        if self._raw is not None and 'local' in self._raw.keys():
            if 'pxref' in self._raw['local'].keys():
                if self._raw['local']['pxref'] is not None:
                    return self._raw['local']['pxref']
        if 'pxref' in self._raw.keys():            
            if self._raw['pxref'] is not None: 
                return self._raw['pxref'][0]
        return None

    def setPXref( self, xref):
        """Local modification of the object primary cross-reference. Setting it 
        to None reverts the modification.
        """
        if self._raw is not None:
            if 'local' not in self._raw.keys():
                self._raw['local'] = {}
            self._raw['local']['pxref'] = xref
            
    @property
    def sxref( self ):
        """A list of secondary cross-references of the object.  
        Corresponds to the list of <xref><secondaryRef/></xref> 
        elements in a PSI-MI XML file.
        """
        sxref = []
        
        if self._raw is not None:

            # overwrite original sxref list if local list set
            if 'local' not in self._raw.keys():
                self._raw['local'] = {}
            if 'sxref_ovr' in self._raw['local'].keys():
                sxref = copy.copy(self._raw['local']['sxref_ovr'])
            else:
                if 'sxref' in self._raw.keys():
                    sxref = copy.copy(self._raw['sxref'])

            # 'sxref_sup' supplements the list with local xrefs
            if 'sxref_sup' in self._raw['local'].keys():
                if self._raw['local']['sxref_sup'] is not None:
                    for x in self._raw['local']['sxref_sup']:
                        sxref.append( x )
            return sxref
        return None                
        
    def supSXref( self, xref):
        """Appends cross-reference the local list of secondary 
        references *supplementing* the initial values. Setting it to None
        clears the supplement list.
        """
        if self._raw is not None:
            if 'local' not in self._raw.keys():
                self._raw['local'] = {}
            if 'sxref_sup' not in self._raw['local'].keys():
                self._raw['local']['sxref_sup'] = []                
            if xref is None:
                self._raw['local']['sxref_sup'] = []
            else:
                self._raw['local']['sxref_sup'].append(xref)
        
    def ovrSXref( self, xref):
        """Appends cross-reference the the local list of secondary 
        references *overwriting* the initial values. Setting it to None
        clears the overwrite list.
        """
        if self._raw is not None:
            if 'local' not in self._raw.keys():
                self._raw['local'] = {}
            if 'sxref_ovr' not in self._raw['local'].keys():
                self._raw['local']['sxref_ovr'] = []                
            if xref is None:
                self._raw['local']['sxref_ovr'] = []
            else:
                self._raw['local']['sxref_ovr'].append(xref)
    
    def getSupSXref( self ):
        """Returns the local list of secondary references *supplementing* 
        the initial values.
        """
        if self._raw is not None:
            if 'local' in self._raw.keys():
                if 'sxref_sup' in self._raw['local'].keys():
                    return self._raw['local']['sxref_sup']
        return None
                
    def getOvrSXref( self ):
        """Returns the local list of secondary references *overwritting* 
        the initial values. Set it to None to discard the changes.
        """
        if self._raw is not None:
            if 'local' in self._raw.keys():
                if 'sxref_ovr' in self._raw['local'].keys():
                    return self._raw['local']['sxref_ovr']
        return None
    
    def xref( self, db ):
        """Returns a list of cross-references to the requested database"""
        xref = []
        if self._raw['pxref'][0]['ns'] == db:
            xref.append(self._raw['pxref'][0])
            
            for s in self._raw['sxref']:
                if s['ns'] == db:
                    xref.append(s)
                    return xref
