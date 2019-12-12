from lxml import etree as ET

import copy
import json
import psimi

class Interaction():

    def __init__( self,  i11n = None , root = None):
        self.ns = { 'mif': 'http://psi.hupo.org/mi/mif' }
        self.__root = root  # parent record 
        self.__int = i11n   # parent interaction

        # local modifications

        self.__label = None
        self.__name = None
        self.__imex = None
        self.__itype = None        
        self.__evlist = None
        self.__pxref = None
        self.__sxref_ovr = None  # overwrite sxref list
        self.__sxref_sup = None  # supplement sxref list
                 
    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        rep=[]
        rep.append("Interaction:")
        rep.append(" Label:\t" + str(self.label))
        rep.append(" Name:\t" + str(self.name))
        rep.append(" Imex ID:\t" + str(self.imex ))        
        rep.append(" Type:\t" + str(self.type))
        rep.append(" PXref:\t" + str(self.pxref) )
        rep.append(" SXref:\t" + str(self.sxref) )
        rep.append(" Attr:\t" + str(self.attrib) )

        rep.append('')        
        rep.append( repr( psimi.Source(self.root['source'], self.root)) )

        if self.isTrimmed: 
            tlen = str( len(self.__int['trimmed']) )
        else:
            tlen = ''

        if self.__int['p11t'] is not None:
            alen = str(len(self.__int['p11t']))
        else:
            alen = '0'
            
        rep.append( " Participant List:\ttrim: " + str(self.isTrimmed) + " " +tlen +"/" + alen )
        for pto in self.ptolist:
            rep.append( repr(pto) )
        rep.append("\n Evidence List:")
        for evo in self.evolist:   
            rep.append( repr(evo) )
            
        return '\n'.join(rep)

    @property
    def root(self):
        return self.__root

    @property
    def int(self):
        return self.__int

    @property
    def imex( self ):
        if self.__imex is not None:  # local override 
            if self.__imex == '':
                return None
            else:
                return self.__imex  
        
        if 'imex' not in self.__int.keys():
            self.__int['imex'] = None   
        
        return self.__int['imex']        
    
    def setImex(self, imex):        
        self.__imex = imex
    
    @property
    def isTrimmed( self ):
        if 'trimmed' not in self.__int.keys():
            self.__int['trimmed'] = None
            
        return self.__int['trimmed'] is not None
    
    @property
    def ptlist( self ):        
        if 'trimmed' not in self.__int.keys():
            self.__int['trimmed'] = None        
        
        if self.__int['trimmed'] is not None:
            return self.__int['trimmed']
        else:
            return self.__int['p11t']

    @property
    def ptall( self ):
        return self.__int['p11t']
    
    @property
    def ptolist( self ):
        ptolst = []
        for pt in self.ptlist:
            ptolst.append( psimi.Participant(pt) )
        return ptolst

    @property
    def ptoall( self ):
        ptolst = []
        for pt in self.ptall:
            ptolst.append( psimi.Participant(pt) )
        return ptolst
    
    @property
    def evlist( self ):
        if self.__evlist is not None:  # local override 
            return self.__evlist 
        
        if 'e10t' not in self.__int.keys():
            self.__int['e10t'] = None   
        
        return self.__int['e10t']        

    def setEvlist(self, evlist):        
        self.__evlist = evlist
   
    @property
    def evolist( self ):    
        evolst = []
        for ev in self.evlist:
            evolst.append( psimi.Evidence( ev ) )
        return evolst                   
         
    @property
    def label( self ):
        if self.__label is not None:
            if self.__label == '':
                return None
            else:
                return self.__label           
        if 'label' in self.__int.keys():
            return self.__int['label']    
        return None

    def setLabel( self, label):
        self.__label = label
    
    @property
    def name( self ):
        if self.__name is not None:
            if self.__name == '':
                return None
            else:
                return self.__name        
        if 'name' in self.__int.keys():            
            return self.__int['name']        
        return None        

    def setName( self, name):
        self.__name = name
    
    @property
    def type( self ):
        if self.__itype is not None:
            if self.__itype == {}:
                return None
            else:
                return self.__itype
            
        if 'itype' in self.__int.keys():
            return self.__int['itype']
        else:
            self.__int['type'] = None
            return None
        
    def setType( self, itype):
        self._itype = itype

    @property
    def pxref( self ):
        if self.__pxref is not None: 
            return self.__pxref        
        if 'pxref' in self.__int.keys():            
            if self.__int['pxref'] is not None: 
                return self.__int['pxref'][0]
        return None
    
    @property
    def sxref( self ):

        if self.__sxref_ovr is not None:
            return self.__sxref_ovr

        if 'sxref' in self.__int.keys():
            sxref = copy.copy(self.__int['sxref'])
            if self.__sxref_sup is not None:
                for x in self.__sxref_sup:
                    sxref.append( x )
            return sxref
        return None

    def supSXref( self, xref): 
        if self.__sxref_sup is None:
            self.__sxref_sup = []
        self.__sxref_sup.append(xref)
        
    def ovrSXref( self, xref):
        if self.__sxref_ovr is None:
            self.__sxref_ovr = []
        self.__sxref_ovr.append(xref)

    def getSupSXref( self ):  
        return elf.__sxref_sup
        
    def getOvrSXref( self ):  
        return elf.__sxref_ovr

    @property
    def attrib( self ):
        """Attribute list."""
        if 'attList' in self.__int.keys():
            return self.__int['attList']
        else:
            return None

    @property
    def attlist( self ):
        return self.attrib
        
    @property
    def modelled( self ):
        if 'modelled' in self.__int.keys():
            return self.__int['modelled']
        else:
            return None

    @property
    def negative( self ):
        if 'negative' in self.__int.keys():
            return self.__int['negative']
        else:
            return None

    @property
    def intramol( self ):
        if 'intramol' in self.__int.keys():
            return self.__int['intramol']
        else:
            return None
        
    def xref( self, db ):
        return self.__int['type']
    
    @property
    def mif25( self ):
        if self.__int['dom'] is not None:
            return str(ET.tostring(self.__int['dom']),'utf-8')
        return ''
