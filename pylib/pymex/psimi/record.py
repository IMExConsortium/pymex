import sys
import json
import psimi
from lxml import etree as ET

class Record():
    """Interaction record. Corresponds to a single <entry>...</entry> element
    of a PSI-MI XML record.
    """
    def __init__( self, root=None ):
        self.ns = { 'mif': 'http://psi.hupo.org/mi/mif' }
        self._root = root
        
        self.etk = []
        self.etl = []
        
        self.irk = []
        self.irl = []

        self.ink = []
        self.inl = []

        self.aek = []
        self.ael = []
        
    @property
    def root( self ):
        return self._root
    
    def __str__(self):
        return self.__repr__()
    
    def __repr__(self):        
        rep=[]
        rep.append("Record:")
        rep.append( repr( psimi.Source(self._root['source'], self._root) ) )
        rep.append(" Interactions:")        
        for i in self.inlist:       
            rep.append(repr(i))
            
        return '\n'.join(rep)

    def addInteraction( self, nint ):
        if isinstance( nint, psimi.interaction.Interaction ):
            self.inl.append(nint)
        else:
            self.inl.append(psimi.Interaction(nint, self._root))
    
    @property
    def imex( self ):

        if len(self.etk) == 0:  # memoize evid keys
            self.etk = list(self._root["e10t"].keys())
            
        if len(self.etk) > 0:
            if 'imex' in  self._root["e10t"][self.etk[0]]:
                return self._root["e10t"][self.etk[0]]['imex']
        
        return ''

    @property
    def pubmed( self ):
        if len( self.etk ) == 0:  # memoize evid keys
            self.etk = list(self._root["e10t"].keys())

        if len(self.etk) > 0:
            return self._root["e10t"][self.etk[0]]['pmid']
        else:
            return ''
    @property
    def aelist(self):

        if len( self.etk ) == 0:  # memoize evid keys
            self.etk = list(self._root["e10t"].keys())

        if len(self.etk) > 0:
            e0 = self._root["e10t"][self.etk[0]]

            if 'attList' in e0:
                return e0['attList']              
        return []

    def attribute( self, name):

        if len( self.etk ) == 0:  # memoize evid keys
            self.etk = list(self._root["e10t"].keys())

        if len(self.etk) > 0:
            e0 = self._root["e10t"][self.etk[0]]

            if 'attList' in e0:
                al = e0['attList']

                for att in al:
                    if att['name'] == name:
                        return att
        return {}

    @property
    def irlist( self ):
        if( len( self.irl) ) == 0:
            self.irk = list(self._root["i10r"].keys())
            
            for ir in self.irk:
                self.irl.append( psimi.Interactor( self._root["i10r"][ir] ))
                    
        return self.irl

    @property
    def inklist( self ):       
        return self._root["i11n"]

    @property
    def inlist( self ):
        
        ilst = []
        for i in self.inklist:
            ilst.append( psimi.Interaction(  self._root["i11n"][i], self._root ))
        return ilst

    
    @property
    def etlist( self ):
        if( len( self.etl) ) == 0:
            self.etk = list(self._root["e10t"].keys())

            for et in self.etk:
                self.etl.append( psimi.Experiment( self._root["e10t"][et] ))
                            
        return self.etl

    @property
    def source( self ):
        return self._root['source']

    @property
    def seo( self ):
        return psimi.Source( self._root['source'], self._root )




    
