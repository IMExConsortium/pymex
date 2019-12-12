import copy
import json
import psimi
from lxml import etree as ET

class Experiment( psimi.Base ):
    """Description of an experiment demonstrating interaction. 
    Corresponds to <experiment>...</experiment> element of a 
    PSI-MI XML record.
    """
    def __init__( self, e10t=None, root=None,  ):
        super(Experiment, self).__init__(raw=e10t, root=root)

    def __repr__(self):
        rep=[]
        rep.append( "  Experiment:" )
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

    @classmethod
    def fromEvidence( cls, evid ):
        """Constructs Experiemnt from Evidence object describing 
        a single-experiment interaction evidence
        """ 
        if evid.etype is None or evid.etype['ac'] != 'ECO:0000021':
            raise psimi.EvidTypeError
        
        nexp = cls( evid.exp, evid.root )

        # copy local mods

        #nexp._label = copy.copy(evid._label)
        #nexp._name = copy.copy(evid._name)

        #nexp._pxref = copy.deepcopy(evid._pxref)
        #nexp._sxref_ovr = copy.deepcopy(evid._sxref_ovr)
        #nexp._sxref_sup = copy.deepcopy(evid._sxref_sup)
                                                
        return nexp
    
    @property
    def exp(self):
        """Raw experiment record data structure.
        """
        return self._raw

    @property
    def pmid( self ):
        """PubMed identifier of the publication describing the experiment.
        """
        if 'pmid' in self._raw.keys():
            return self._raw['pmid']
        else:
            return None

    @property
    def bibref( self ):
        """Full bibliographic reference of the publication describing 
        the experiment. Corresponfs to <bibref>...</bibref> element of
        a PSI-MI XML record.
        """
        if 'bibref' in self._raw.keys():
            return self._raw['bibref']
        else:
            return None

    @property
    def imex( self ):
        """Imex Consortium unique identifier of the interaction dataset.
        """ 
        if 'imex' in self._raw.keys():
            return self._raw['imex']
        else:
            return None

    @property
    def ehost( self ):
        """A list of experiment hosts. Corresponds to the list of 
        <hostOrganismList><hostOrganism>...</hostOrganism></hostOrganismList>
        elements in PSI-MI XML record.
        """
        if 'ehost' in self._raw.keys():                   
            return self._raw['ehost']
        else:
            return None

    @property
    def intMth( self ):
        """Interaction detection method. Corresponds to the 
        <interactionDetectionMethod>...</interactionDetectionMethod> element
        in  PSI-MI record.
        """
        if 'intMth' in self._raw.keys():
            return self._raw['intMth']
        else:
            return None

    @property
    def prtMth( self ):
        """Participant identification method. Corresponds to the 
        <participantIdentificationMethod>...</participantIdentificationMethod> 
        element in  PSI-MI record.
        """
        if 'prtMth' in self._raw.keys():
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
