import json
from pymex import psimi as psimi
#import psimi

class PsiMiConvert():
        
    def __init__( self, record = None ):
        self.ns = { 'mif': 'http://psi.hupo.org/mi/mif' }
        self.prtrimlst = ['MI:0684']  # participant role trim list (skip if on the list)
        self.ixkeeplst = ['MI:0460', 'MI:0806', 'MI:0472', 'MI:0805', 'MI:0936', 'MI:2017',
                          'MI:0448',
                          'MI:0449',
                          'MI:0467',
                          'MI:0476',
                          'MI:0471'] # interactor xref trim (pdb, go, interpro, reactome, mint, ensembl)
        self.nomatrix = ['MI:0914']   # nomatrix expansion list (default: association) 
        self.bait = ['MI:0496']   # bait
        self.prey = ['MI:0498']   # prey

        self.const = { 'CV' : {}, 'AT':{}, 'XR': {} }
        
        self.const['CV']['phys-ass'] = {'ns': 'psi-mi',
                                        'label': 'physical association',
                                        'name': 'physical association',
                                        'nsAc': 'MI:0488', 'ac': 'MI:0915'}
        
        self.const['XR']['imex-inf'] = {'nsAc': 'MI:00670', 'ns': 'imex',
                                        'ac': '', 
                                        'refType': 'inferred-from',
                                        'refTypeAc':'MI:1351'}
        
        self.const['AT']['dir-ev'] = {'name': 'evidenceType', 'value': 'direct assay' } 
        self.const['AT']['spoke-ev'] = {'name': 'evidenceType', 'value': 'spoke expansion' } 
        self.const['AT']['matrix-ev'] = {'name': 'evidenceType', 'value': 'matrix expansion' } 
        self.const['AT']['semi-ev'] = {'name': 'evidenceType', 'value': 'semi-interolog' } 
 
        if isinstance(record, psimi.record.Record):            
            self._root = record.root
        else:                        
            self._root = record
        
        self.etk = []
        self.etl = []
        
        self.irk = []
        self.irl = []

    @property    
    def root( self ):
        return self._root

    @property
    def inklist( self ):
        return self._root.mif["i11n"]

    @property
    def ptrimList(self):
        """The list of experimental role accessions used to trim participant
        list. 
        """
        return self.prtrimlst

    def setPTrimList(self, trimlist):
        """Set participant trim list.
        """
        self.prtrimlst = trimlist
        
    def trim( self, ink = None ):  #  remove noninteracting entities
        """Remove participants with experimental role accession matching 
        ptrim list. 
        """
        if ink is None:
            inklst = self._root["i11n"].keys()
        else:
            inklst = [ ink ]

        intlst = []
        
        for i in inklst:
            ino = self._root["i11n"][i]
            ino['trimmed'] = []
        
            for p in ino['p11t']:

                keep = True
                
                for er in p['erole']:
                    if er['ac'] in self.prtrimlst:
                        keep = False
                        break

                if keep:
                    ino['trimmed'].append(p)

            intlst.append( psimi.Interaction( ino, self._root ))
                
        return intlst 
   
    def untrim( self, ink = None ):  #  undo trim
        """Revert participant trim operation.
        """
        if ink is None:
            inklst = self._root["i11n"].keys()
        else:
            inklst = [ ink ]

        intlst = []
        
        for i in inklst:
            ino = self._root["i11n"][i]
        
            if 'trimmed' in ino:
                ino['trimmed'] = None

            intlst.append( psimi.Interaction( ino, self._root ))
                
        return intlst 

    @property
    def ixkeepList(self):
        """The list of reference sources to retain when ixtrimming interaction 
        secondary cross-references.
        """
        return self.ixkeeplst

    def setIXKeepList(self, keeplist):
        """Set reference sources to be retained when ixtrimming interaction 
        secondary cross-references.
        """
        self.ixkeeplst = keeplist
        
    def ixtrim( self, irk = None ):  #  remove interactor crossrefs
        """Trim interactor secondary cross-reference list retaining only these
        that match resources with accessions on the ixtrimList.
        """
        if irk is None:
            irklst = self._root["i10r"].keys()
        else:
            irklst = [ irk ]

        irlst = []
        
        for i in irklst:
            iro = psimi.Interactor( self._root["i10r"][i], self._root )
            for sx in iro.raw['sxref']: # go over the initial sxref list
                if sx['nsAc'] not in self.ixkeeplst:                    
                    iro.ovrSXref( sx )                    
            irlst.append( iro  )
            
        return irlst 

    def ixuntrim( self, irk = None ):  #  undo trim
        """Revert interactor cross-reference trim operation. 
        """
        if irk is None:
            irklst = self._root["i10r"].keys()
        else:
            irklst = [ irk ]

        irlst = []
        
        for i in irklst:
            iro = psimi.Interactor( self._root["i10r"][i], self._root )        
            iro.supSXref(None)

            irlst.append( iro )
        return irlst     
           
    def spoke( self, label = None ):  #  spoke expansion
        """Spoke expand interactions. Returns only expanded binary
        interactions.
        """
        # expands:
        #   - only associations (accession NOT in nomatrix)
        #   - only non-ancillaries (acessions NOT in prtrimlst)

        brec = psimi.Record( self._root ) # this sets source 

        inklst = self._root["i11n"].keys()

        binolist = [] 
        sinklst = []        
        for i in inklst:
            # go over interactions
            if label is None or (label == self._root["i11n"][i]['label']):
                sinklst.append(i)
        
        for i in sinklst:
            # go over interactions
            ino = psimi.Interaction( self._root["i11n"][i], self._root )
            
            if ino.type['ac'] in self.nomatrix:
                continue 
            ptolist = []
            mxlist = []

            baitPto = []
            allPto = []
            
            for p in ino.ptlist:
                pto = psimi.Participant( p, self._root )
                if pto.erole is not None:
                    for er in pto.erole:
                        if er['ac'] in self.bait:
                            baitPto.append(pto)
                            break                            
                    for er in pto.erole:
                        if er['ac'] in self.prtrimlst:
                            continue
                        else:
                            allPto.append(pto)
                
            for pto1 in baitPto:
                for pto2 in allPto:
                    # valid binary here
                    if pto1 != pto2:  
                        #print ( pto2.ilabel +">"+ pto1.ilabel)
                        bin = {}
                        
                        for k in self._root["i11n"][i]:
                            bin[k]=self._root["i11n"][i][k]

                        # binary interaction                        
                        bin['trimmed'] = [ pto1.prt, pto2.prt ]

                        # updated evidence ?
                                                
                        # updated type: association ->  physical
                        
                        
                        bino = psimi.Interaction( bin, self._root )

                        # unset imex id set reference if imex was preset
                        imexId = bino.imexId
                        if imexId is not None and imexId !='':
                            bino.setImex(None) 

                            
                        
                        brec.addInteraction( bino )
        #return brec
        return brec.inlist

    def matrix( self, label = None ):  #  matrix expansion
        """Matrix expand interactions. Returns only expanded binary
        interactions. 
        """        
        binolist = []
        sinklst = [] 

        inklst = self._root["i11n"].keys()
                
        for i in inklst:
            # go over interactions
            if label is None or (label == self._root["i11n"][i]['label']):
                sinklst.append(i)
                
        brec = psimi.Record( self._root ) # this sets source 
               
        for i in sinklst:
            # go over interactions
            ino = psimi.Interaction( self._root["i11n"][i], self._root )
            
            if ino.type['ac'] in self.nomatrix:
                continue 
            ptolist = []
            mxlist = []
            
            for p in ino.ptlist:
                pto = psimi.Participant( p, self._root )
                if pto.erole is not None:
                    for er in pto.erole:
                        if er['ac'] in self.prtrimlst:
                            continue
                        else:
                            ptolist.append(pto)
                                  
            if len(ptolist) < 3:
                continue
            
            for pto1 in ptolist:
                for pto2 in ptolist:
                    # valid binary here
                    if pto2.ilabel > pto1.ilabel:
                        #print ( pto2.ilabel +">"+ pto1.ilabel)
                        bin = {}
                        
                        for k in self._root["i11n"][i]:
                            bin[k]=self._root["i11n"][i][k]

                        # binary interaction     
                        bin['trimmed'] = [ pto1.prt, pto2.prt ]

                        # updated evidence
                                                
                        # updated type
                    
                        bino = psimi.Interaction( bin, self._root )

                        # unset imex id set reference if imex was preset
                        imexId = bino.imexId
                        if imexId is not None and imexId !='':
                            bino.setImex(None) 
                        
                        brec.addInteraction( bino )
        return brec.inlist
