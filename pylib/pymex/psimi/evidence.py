import copy
import json
import psimi
from lxml import etree as ET

class Evidence(psimi.Base):
    """Description of evidence demonstrating interaction. At the moment, 
    only a wrapper around psimi.Experiment, which constitutes 
    a single-experiment interaction evidence. 
    """
    def __init__( self, e10t=None, root=None ):
        super(Evidence, self).__init__(raw=e10t,  root=root)
        self._etype =  {'ns': 'eco',
                        'ac': 'ECO:0000021',
                        'nsAc': None,
                        'name': 'physical interaction evidence',
                        'label': 'interaction evidence'}
    
    def __repr__(self):
        rep=[]
        rep.append( "  Evidence:" )
        rep.append( "   Label: " + str(self.label)  )
        rep.append( "   Name: " + str(self.name)  )
        rep.append( "   PMID: " + str(self.pmid)  )
        rep.append( "   Imex: " + str(self.imex)  )
        rep.append( "   PXref: " + str(self.pxref)  )
        rep.append( "   SXref: " + str(self.sxref)  )
        rep.append( "   IntMth: " + str(self.intMth)  )
        rep.append( "   PrtMth: " + str(self.prtMth)  )
        rep.append( "   Exp Host: " + str(self.ehost)  )
        return '\n'.join(rep)

    @property
    def exp(self):
        """Raw evidence data structure.
        """
        return self._raw
    
    @property
    def pmid( self ):
        """A list of PubMed identifiers of the publications describing 
        the experiments.
        """
        if 'pmid' in self._raw.keys():
            return self._raw['pmid']
        else:
            return None

    @property
    def bibref( self ):
        """A list of full bibliographic references to the publications 
        describing experiments contributing to the evidence. 
        """
        if 'bibref' in self._raw.keys():
            return list(self._raw['bibref'])
        else:
            return None

    @property
    def imex( self ):
        """A list of unique Imex Consortium identifiers of the interaction 
        datasets contributing to this evidence.
        """
        if 'imex' in self._raw.keys():
            return self._raw['imex']
        else:
            return None

    @property
    def ehost( self ):
        """A list of experiment hosts.
        """
        if 'ehost' in self._raw.keys():
            return list(self._raw['ehost'])
        else:
            return None

    @property
    def etype( self ):
        """Evidence type provides information about the method used
        to infer interaction from one or more pieces of experimental
        data and/or other observations. Currently, only conclusions
        based on a single experiment are supported.
        """
        
        return self._etype
    
    @property
    def intMth( self ):
        """A list of interaction detection methods.
        """
        if 'intMth' in self._raw.keys():
            #return list(self._raw['intMth'])
            return self._raw['intMth']
        else:
            return None
        
    @property
    def prtMth( self ):
        """A list of participant identification methods.
        """
        if 'prtMth' in self._raw.keys():
            #return list(self._raw['prtMth'])
            return self._raw['prtMth']
        else:
            return None
        
    @property
    def attrib( self ):
        """Attribute list."""
        if 'attList' in self._raw.keys():
            return self._raw['attList']
        else:
            return None
