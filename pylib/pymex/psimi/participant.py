import copy
import json
import psimi
from lxml import etree as ET 

class Participant(psimi.Base): 
    """Biomolecule form as used in the experiment. Corresponds to
    <participant>...</participant> element of the PSI-MI XML record.
    """
    def __init__( self, prt=None, root=None ):
        super(Participant, self ).__init__( raw = prt, root = root)
        
    def __repr__(self):
        rep=[]
        rep.append("  Participant:")
        rep.append("   Label:\t" + str(self.ilabel))
        rep.append("   Name:\t" + str(self.iname))
        rep.append("   Species:\t" + str(self.ispecies))
        rep.append("   IPXref:\t" + str(self.ipxref))
        rep.append("   ISXref:\t" + str(self.isxref))
        rep.append("   PXref:\t" + str(self.pxref))
        rep.append("   SXref:\t" + str(self.sxref))
        if self.ehost:
            rep.append("   Exp Host:\t" + str(self.ehost))
        else:
            rep.append("   Exp Host:\t" + str(self.ispecies))
        rep.append("   Exp Prep:\t" + str(self.eprep))
        rep.append("   Exp Role:\t" + str(self.erole))
        rep.append("   Bio Role:\t" + str(self.brole))
        rep.append("   Features:\t" + str(self.feature))            
        rep.append("")
        return '\n'.join(rep)

    @property
    def interactor(self):
        """psimi.Interactor object representing the reference version of
        the biomolecule.
        """ 
        return psimi.Interactor(self._raw['i10r'], self._root)

    @property
    def prt(self):
        """Raw participant record data structure.
        """        
        return self._raw
    
    @property
    def iname( self ):
        """Interactor name
        """
        if 'name' in self._raw['i10r'].keys():
            return self._raw['i10r']['name']
        return None
            
    @property
    def ilabel( self ):
        """Interactor short(er) label
        """
        if 'label' in self._raw['i10r']:
            return self._raw['i10r']['label']
        else:            
            return self._raw['i10r']['pxref'][0]['ac']

    @property
    def ispecies( self ):
        """Interactor species. Native species the biomolecule is made in"""
        if 'species' in self._raw['i10r'].keys():
            if self._raw['i10r']['species'] is not None:                  
                return self._raw['i10r']['species']
        return None

    @property
    def ehost( self ):
        """Experimental host list. The list of the organism(s) that the 
        biomolecule used in the experiment was produced in.
        """
        if 'ehost' in self._raw.keys():
            return list(self._raw['ehost'])
        return None
        
    @property
    def erole( self ):
        """Experimental role list . The list of experimental roles 
        (e.g. bait, prey) of the participant in the experiment.
        """ 
        if 'erole' in self._raw.keys():
            return self._raw['erole']
        
        self.prt['erole'] = None            
        return None

    @property
    def brole( self ):
        """Biological role. The biological role of the participant
        (e.g. enzyme, enzyme target0, as used in the experiment.
        """
        if 'brole' in self._raw.keys():
            return self._raw['brole']
        else:
            self.__prt['brole'] = None            
            return None

    @property
    def eprep( self ):
        """Experimental preparation (list). Terms describing experimental
        preparation of the participant.
        """
        if 'eprep' in self._raw.keys():
            return self._raw['eprep']
        else:
            self._prt['eprep'] = None            
            return None

    @property
    def pidmth( self ):
        """Participant identification method (list). The methods used to
        identify the molecule as participating in the interactions.
        """
        if 'pidmth' in self._raw.keys():
            return self._raw['pidmth']
        else:
            self._raw['pidmth'] = None            
            return None
         
    @property
    def ipxref( self ):
        """Primary cross-reference of the interactor.
        """
        return self.interactor.pxref

    @property
    def isxref( self ):
        """Secondary cross-references of the interactor. 
        """
        return self.interactor.sxref
       
    @property
    def attrib( self):
        """Attribute list.
        """
        if 'attrib' in self._raw.keys():
            return self._raw['attrib']
        else:
            return None

    @property
    def feature( self ):
        """A list of raw records describing features relavant for the
        experiment that demonstrated described interaction.
        """
        if 'feature' in self._raw.keys():
            return self._raw['feature']
        else:
            return None

    @property
    def frolst( self ):
        """A list of psimi.Feature objects describing features relavant
        for the experiment that demonstrated described interaction.
        """
        if 'feature' in self._raw.keys() and len( self._raw['feature']) > 0:
            frolst = []
            for fr in self._raw['feature']:
                frolst.append(psimi.Feature(fr, self._root ) )
            return frolst    
        return None

    
