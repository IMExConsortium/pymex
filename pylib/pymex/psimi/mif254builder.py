import json
from lxml import etree as ET
import psimi

class Mif254Builder():
    """Builds PSI-MI XML (ver 2.5.4) representation of interaction record
    as a single entry <entrySet>.
    """
    def __init__(self):
        self.ns="http://psi.hupo.org/mi/mif"
        self.nsmap = {None: self.ns }
        self.mif = "{%s}" % self.ns
        self.dom = ET.Element( self.mif + "entrySet", nsmap = self.nsmap)
        self._doc = {}
        self.id = 1

        self.dom.attrib['level']="2" 
        self.dom.attrib['version']="5"
        self.dom.attrib['minorVersion']="4" 
        
        self._doc['entry'] = ET.SubElement( self.dom, self.mif + "entry" )
        self._doc['source'] = None  # <source>           : required
        self._doc['etlst'] = None   # <experimentList>   : optional
        self._doc['irlst'] = None   # <interactorList>   : optional
        self._doc['inlst'] = None   # <interactionList>  : required 
        self._doc['aelst'] = None   # <AttributeList>    : optional

    @property
    def source( self ):
        """<source> DOM element.
        """
        return self._doc['source']

    @property
    def irlst( self ):
        """<interactorList> DOM element.
        """
        return self._doc['irlst']
    
    @property
    def inlst( self ):
        """<interactionList> DOM element.
        """
        return self._doc['inlst']

    @property
    def etlst( self ):
        """<experimentList> DOM element.
        """
        return self._doc['etlst']

    @property
    def aelst( self ):
        """<attributeList> DOM element.
        """
        return self._doc['aelst']
            
    @property
    def docStr( self ):
        """Serialized (PSI-MI XML ver 2.5.4) record representation
        """
        return str(ET.tostring(self.dom, pretty_print=True),'utf-8')

    def buildRecord( self, rec):
        """Builds PSI-MI XML 2.5.4 record representation. 
        """

        #print("****")
        if not isinstance( rec, psimi.record.Record ):
            raise TypeError

        # set source        
        self.addSource( rec.seo )
        
        # set interactions
        if rec.inlist is not None and len(rec.inlist) > 0:        
            for i in rec.inlist:
                self.addInteraction( self._doc['inlst'], i)
                
        # set attributes
        #if rec.aelist is not None and len(rec.aelist) > 0:        
        #    self.addAttList(self._doc['entry'], rec.aelst )

        if rec.aelist is not None and len(rec.aelist) > 0:
            for ai in rec.aelist:
                self.addAttribute(self._doc['aelst'], ai )
            
    def addSource( self, src):
        """Add psimi.Source representation.
        """
        if not isinstance(src, psimi.source.Source):
            raise TypeError
        # names
        if self._doc['source']  is None:
            self._doc['source'] = ET.SubElement( self._doc['entry'],
                                                self.mif + "source" )
        self.addNames( self._doc['source'], src.label, src.name )

        # bibref
        if src.bibref is not None:
            #print(src.bibref)
            self.addBibref(  self._doc['source'], src.bibref )

        # xref
        self.addXref( self._doc['source'], src.pxref, src.sxref)

        #attribute
        self.addAttList(self._doc['source'], src.attlst )
    
    def addExperiment( self, parent, evid):
        """Adds psimi.Experiment representation to parent element DOM. If parent 
        is None it is initialized as an entry-level <experimentList>.
        """
        if not isinstance(evid, psimi.evidence.Evidence):
            raise TypeError

        # only simple evidence supported
        nexp = psimi.Experiment.fromEvidence( evid )

        if parent is None:
            parent = ET.SubElement( self._doc['etlst'],
                                    self.mif + "experimentList" )
        
        ev0 = ET.SubElement( parent, self.mif + "experimentDescription" )
        ev0.attrib['id']= str(self.id)
        self.id+=1

        #Label: mcevoy-1998-1
        #Name: mcevoy-1998-1
        #Imex: IM-26977
        #PXref: {'refType': 'identity', 'refTypeAc': 'MI:0356',
        #        'ns': 'intact', 'nsAc': 'MI:0469', 'ac': 'EBI-21200115'}
        #SXref: [{'refType': 'imex-primary', 'refTypeAc': 'MI:0662',
        #         'ns': 'imex', 'nsAc': 'MI:0670', 'ac': 'IM-26977'}]
        #IntMth: {'name': 'x-ray diffraction', 'label': 'x-ray diffraction',
        #         'ns': 'psi-mi', 'nsAc': 'MI:0488', 'ac': 'MI:0114'}
        #PrtMth: {'name': 'experimental particp', 'label': 'experimental particp',
        #         'ns': 'psi-mi', 'nsAc': 'MI:0488', 'ac': 'MI:0661'}
        #Exp Host: [{'name': 'In vitro', 'label': 'in vitro', 'ns': 'taxid', 'ac': '-1'}]

        # names
        self.addNames( ev0, nexp.label, nexp.name )

        # bibref
        if evid.pmid is not None:
            br0 = ET.SubElement( ev0, self.mif + "bibref" )
            self.addXref( br0, {'ns':'pubmed','nsAc':'MI:0446',
                                'ac':nexp.pmid,
                                'refType':'primary-reference',
                                'refTypeAc':'MI:0358'})

        # bibref
        if evid.bibref is not None:
            self.addBibref(  ev0, nexp.bibref )
            
        # xref
        self.addXref( ev0, nexp.pxref, nexp.sxref)
        
        #hostOrganismList      
        #  hostOrganism

        if nexp.ehost is not None:
            hol = ET.SubElement( ev0, self.mif + "hostOrganismList" )
            for ho in nexp.ehost:
                self.addOrganism( hol, ho, ename='hostOrganism')

        #interactionDetectionMethod
        if nexp.intMth is not None:
            self.addCvTerm( ev0, nexp.intMth, ename='interactionDetectionMethod')
            
        #participantIdentificationMethod
        if nexp.prtMth is not None:
            self.addCvTerm( ev0, nexp.prtMth, ename='participantIdentificationMethod')
                        
        #attributeList
        self.addAttList(ev0, nexp.attrib )
        
    def addParticipant( self, parent, prt):
        """Adds psimi.Participant representation to parent element DOM.
        """       
        if not isinstance(prt, psimi.participant.Participant):
            raise TypeError

        if parent is None:
            raise MissingParentError
        
        pa0 = ET.SubElement( parent, self.mif + "participant" )
        pa0.attrib['id']= str(self.id)
        self.id+=1

        # names: shortLabel & fullName

        label = prt.label
        if label == 'N/A':
            label = None
            
        self.addNames( pa0, label, prt.name )

        # xref: primaryRef & secondaryRef(s)
        self.addXref( pa0, prt.pxref, prt.sxref)

        #interactor
        self.addInteractor( pa0, prt.interactor)
        
        #participantIdentificationMethodList
        #   participantIdentificationMethod
        if prt.pidmth is not None and len(prt.pidmth) > 0:
            pa1 = ET.SubElement( pa0, self.mif + "participantIdentificationMethodList" )
            for pim in prt.pidmth:
                pa2 = self.addCvTerm( pa1, pim, ename='participantIdentificationMethod')
                
        #biological role
        if prt.brole is not None:
            br0 = self.addCvTerm( pa0, prt.brole, ename='biologicalRole')
        
        #experimentalRoleList
        #   experimentalRole
        if prt.erole is not None and len(prt.erole) > 0:
            ex0 = ET.SubElement( pa0, self.mif + "experimentalRoleList" )
            for ero in prt.erole:
                ero1 = self.addCvTerm( ex0, ero, ename='experimentalRole')
                    
        #experimentalPreparationList
        #   experimentalPreparation
        if prt.eprep is not None and len(prt.eprep) > 0:
            ep0 = ET.SubElement( pa0, self.mif + "experimentalPreparationList" )
            for epo in prt.eprep:
                ep1 = self.addCvTerm( ep0, epo, ename='experimentalPreparation')
                        
        #featureList
        #  feature
        if prt.frolst is not None:
            fr0 = ET.SubElement( pa0, self.mif + "featureList" )
            for fro in prt.frolst:
                fr1 = self.addFeature( fr0, fro )
        
        #hostOrganismList      
        #  hostOrganism
        if prt.ehost is not None:
            hol = ET.SubElement( pa0, self.mif + "hostOrganismList" )
            for ho in prt.ehost:
                self.addOrganism( hol, ho, ename='hostOrganism')
     
        #attributeList
        self.addAttList(pa0, prt.attrib )
        
    def addInteraction( self, parent, i11n):
        """Adds psimi.Interaction representation to parent element DOM. 
        If parent is None it is initialized as an entry-level <interactionList>.
        """        
        if not isinstance(i11n, psimi.interaction.Interaction):
            raise TypeError

        if parent is None:
            parent = ET.SubElement( self._doc['entry'],
                                    self.mif + "interactionList" )
        
        ev0 = ET.SubElement( parent, self.mif + "interaction" )
        ev0.attrib['id']= str(self.id)
        self.id+=1
        
        # names: shortLabel & fullName 
        self.addNames( ev0, i11n.label, i11n.name )

        # xref: primaryRef & secondaryRef(s)
        imexid = self.addXref( ev0, i11n.pxref, i11n.sxref)

        if imexid is not None:
            ev0.attrib['imexId']= str(imexid)
        
        # experimentList
        ev2 = ET.SubElement( ev0, self.mif + "experimentList" )

        for evo in i11n.evolist: 
            self.addExperiment( ev2, evo)
        
        # participantList

        ev3 = ET.SubElement( ev0, self.mif + "participantList" )

        for pto in i11n.ptolist:
            self.addParticipant( ev3, pto)

        # interaction Type

        self.addCvTerm( ev0, i11n.type, ename='interactionType')

        if i11n.modelled is not None and i11n.modelled.lower() != 'false':
            ev4 = ET.SubElement( ev0, self.mif + "modelled" )
            ev4.text=i11n.modelled            

        if i11n.intramol is not None and i11n.intramol.lower() != 'false':
            ev5 = ET.SubElement( ev0, self.mif + "intraMolecular" )
            ev5.text=i11n.intramol

        if i11n.negative is not None and i11n.negative.lower() != 'false':
            ev5 = ET.SubElement( ev0, self.mif + "negative" )
            ev5.text=i11n.negative

        # attributes 
        self.addAttList( ev0, i11n.attrib )
    
            

    def addInteractor( self, parent, i10r, seq=True, att=True ):
        """Adds psimi.Interactor representation to parent element DOM.
        If parent is None it is initialized as an entry-level <interactorList>.
        """
        if not isinstance(i10r, psimi.interactor.Interactor):
            raise TypeError

        if parent is None:
            parent = ET.SubElement( self._doc['entry'],
                                    self.mif + "interactorList" )        
        #print(self.__dict__)
        #print(i10r.raw.keys())
        ir0 = ET.SubElement( parent, self.mif + "interactor" )
        ir0.attrib['id']= str(self.id)
        self.id+=1
        
        # names: shortLabel & fullName 
        self.addNames( ir0, i10r.label, i10r.name )

        # xref: primaryRef & secondaryRef(s)
        self.addXref( ir0, i10r.pxref, i10r.sxref)
                    
        # molecule type
        self.addCvTerm( ir0, i10r.type, ename='interactorType' )
        
        # organism
        if i10r.species is not None:
            self.addOrganism( ir0, i10r.species )

        if seq is True and i10r.sequence is not None:
            sq0 = ET.SubElement( ir0, self.mif + "sequence" )
            sq0.text = i10r.sequence

        # attribute list
        if att is True:
            pass
                    
    def addXref( self, parent, pxref=None, sxref=None):
        """Add cross references to parent element DOM.
        """

        imexId = None
        
        # xref: primaryRef & secondaryRef(s)

        if pxref is not None or (sxref is not None and len(sxref) > 0):
            ir0 = ET.SubElement( parent, self.mif + "xref" )

            #{'ver': 'SP_26', 'ns': 'uniprotkb', 'ac': 'P0AE67', 'nsAc': 'MI:0486'}
                        
            if pxref is not None:

                if isinstance(pxref, list):
                    pxref = pxref[0]

                ir1 = ET.SubElement( ir0, self.mif + "primaryRef" )
                if 'ac' in pxref.keys():
                    ir1.attrib['id']=pxref['ac']
                if 'ns' in pxref.keys():
                    ir1.attrib['db']=pxref['ns']
                if 'nsAc' in pxref.keys():
                    ir1.attrib['dbAc']=pxref['nsAc']
                if 'ver' in pxref.keys():
                    ir1.attrib['ver']=pxref['ver']
                if 'refType' in pxref.keys():
                    ir1.attrib['refType']=pxref['refType']
                if 'refTypeAc' in pxref.keys():
                    ir1.attrib['refTypeAc']=pxref['refTypeAc']

                #<secondaryRef id="IM-26977-1" db="imex" dbAc="MI:0670" refType="imex-primary" refTypeAc="MI:0662"/>

                if 'ns' in pxref.keys() and 'ac' in pxref.keys() and 'refType' in pxref.keys():
                    if pxref['ns'] == 'imex' and pxref['refType'] == 'imex-primary':
                        imexId = pxref['ac']

                if 'ns' in pxref.keys() and 'ac' in pxref.keys() and 'refType' not in pxref.keys():
                    if pxref['ns'] == 'dip' and pxref['ac'] is not None and len( pxref['ac']) > 0:
                        ir1.attrib['refType']='identity'
                        ir1.attrib['refTypeAc']='MI:0356'
                                                
            if sxref is not None and len(sxref) > 0:
                for sxr in sxref:
                    ir2 = ET.SubElement( ir0, self.mif + "secondaryRef" )
                    if 'ac' in sxr.keys():
                        ir2.attrib['id']=sxr['ac']
                    if 'ns' in sxr.keys():
                        ir2.attrib['db']=sxr['ns']
                    if 'nsAc' in sxr.keys():
                        ir2.attrib['dbAc']=sxr['nsAc']
                    if 'ver'  in sxr.keys():
                        ir2.attrib['ver']=sxr['ver']
                    if 'refType' in sxr.keys():
                        ir2.attrib['refType']=sxr['refType']
                    if 'refTypeAc' in sxr.keys():
                        ir2.attrib['refTypeAc']=sxr['refTypeAc']

                    if 'ns' in sxr.keys() and 'ac' in sxr.keys() and 'refType' in sxr.keys():
                        if sxr['ns'] == 'imex' and sxr['refType'] == 'imex-primary':
                            imexId = sxr['ac']
                    
                    if 'ns' in sxr.keys() and 'ac' in sxr.keys() and 'refType' not in sxr.keys():
                        if sxr['ns'] == 'dip' and sxr['ac'] is not None and len( sxr['ac']) > 0:
                            ir2.attrib['refType']='identity'
                            ir2.attrib['refTypeAc']='MI:0356'

            #return ir0
        #else:
            # return None
        return imexId

    def addBibref( self, parent, bibref=None ):
        """Add bibref representation to parent element DOM.
        """
        if bibref is None: 
            return

        br0 = ET.SubElement( parent, self.mif + "bibref" )
        
        pxref = None
        sxref = None
        if 'pxref' in bibref.keys() and bibref['pxref'] is not None:
            pxref = bibref['pxref'][0]
        if 'sxref' in bibref.keys():
            sxref = bibref['sxref']
            
        br1 = self.addXref( br0, pxref, sxref)
        if 'attlst' in bibref.keys():
            br2 = self.addAttList( br0, bibref['attlst'] )

        
    # organism/host
    def addOrganism( self, parent, organism, ename='organism'):
        """Add organism representation to parent element DOM. 
        """
        #Species: {'ac': '83333', 'label': 'ecoli', 'ns': 'taxid',
        #          'name': 'Escherichia coli (strain K12)'}

        #<organism ncbiTaxId="9606">
        # <names>
        #  <shortLabel>Human</shortLabel>
        #  <fullName>Home sapiens</fullName>
        # </names>
        # <cellType>
        #  <names>
        #   <shortLabel>293</shortLabel>
        #   <fullName>Transformed human primary embryonal kidney cells.</fullName>
        #  </names>
        #  <xref>
        #   <primaryRef db="mint" dbAc="MI:0471" id="MINT-1782570" refType="identity" refTypeAc="MI:0356"/>
        #   <secondaryRef db="cabri" dbAc="MI:0246" id="ACC 305" refType="identity" refTypeAc="MI:0356"/>
        #  </xref>        
        # </cellType>
        #</organism>

        ir0 = ET.SubElement( parent, self.mif + ename )
        ir0.attrib['ncbiTaxId']= organism['ac']
        ir1 = ET.SubElement( ir0, self.mif + "names" )
        if 'label' in organism.keys():
            ir2 = ET.SubElement( ir1, self.mif + "shortLabel" )
            ir2.text = organism['label']

        if 'name' in organism.keys():
            ir3 = ET.SubElement( ir1, self.mif + "fullName" )
            ir3.text = organism['name']

        if 'ctype' in organism.keys():
            ir4 = ET.SubElement( ir1, self.mif + "cellType" )
            ctype = organism['ctype']
            label = None
            name = None
            
            if 'label' in ctype.keys():
                label = ctype['label']
            if 'name' in ctype.keys():
                name = ctype['name']
            if label is not None or name is not None:
                ir5 = ET.SubElement( ir4, self.mif + "names" )
                if label is not None:
                    ir6 = ET.SubElement( ir5, self.mif + "shortLabel" )
                    ir6.text=label
                if name is not None:
                    ir7 = ET.SubElement( ir5, self.mif + "fullName" )
                    ir7.text=name

            if 'pxref' in ctype.keys():
                pxref = ctype['pxref']
                
            if 'sxref' in ctype.keys():
                sxref = ctype['sxref']

            if pxref is not None or sxref is not None:                
                self.addXref( ir4, pxref, sxref )
                
    def addNames( self, parent, label=None, name=None ):
        """Add label and/or name representation to parent element DOM.
        """

        if parent is None:
            raise MissingParentError

        if label is not None or name is not None:
            na0 = ET.SubElement( parent, self.mif + "names" )

            if label is not None:
                na1 = ET.SubElement( na0, self.mif + "shortLabel" )
                na1.text = label
                
            if name is not None and name != label:
                na2 = ET.SubElement( na0, self.mif + "fullName" )
                na2.text = name

    def addCvTerm( self, parent, term = None, ename=None):
        """Add CV term representation to parent element DOM.
        """
        if ename is None or term is None:
            return

        if parent is None:
            raise MissingParentError
        
        #{'nsAc': 'MI:0488', 'name': 'x-ray diffraction',
        # 'label': 'x-ray diffraction', 'ac': 'MI:0114', 'ns': 'psi-mi'}
        
        cv0 = ET.SubElement( parent, self.mif + ename )
        cv1 = ET.SubElement( cv0, self.mif + "names" )

        if 'label' in term.keys():
            cv2 = ET.SubElement( cv1, self.mif + "shortLabel" )
            cv2.text = term['label']

        if 'name' in term.keys():
            cv2 = ET.SubElement( cv1, self.mif + "fullName" )
            cv2.text = term['name']

        pxref = term.copy() # shallow copy, add ref type info when missing
            
        if 'refType' not in pxref.keys():                
            pxref['refType']="identity"
            
        if 'refTypeAc' not in pxref.keys():
            pxref['refTypeAc'] = "MI:0356"
            
        self.addXref( cv0, pxref )

    # attribute list    
    def addAttList( self, parent, attrib):
        """Add attribute list representation to parent element DOM.
        """
        if attrib is None or len(attrib) == 0:
            return

        al0 = ET.SubElement( parent, self.mif + "attributeList" )
        for at in attrib:
            at0 = ET.SubElement( al0, self.mif + "attribute" )
            if 'value' in at.keys():
                at0.text= at['value']
            if 'name' in at.keys():
                at0.attrib['name']= at['name']
            if 'ac' in at.keys():
                at0.attrib['nameAc']= at['ac']

    def addAttribute( self, parent, attrib):
        """Add attribute representation to parent element DOM. 
        If parent is None it is initialized as an entry-level <attributeList>.
        """        
        
        if attrib is None:
            return
        
        if parent is None:
            parent = ET.SubElement( self._doc['entry'],
                                    self.mif + "attributeList" )
        
        at0 = ET.SubElement( parent, self.mif + "attribute" )
        if 'value' in attrib.keys():
            at0.text= attrib['value']
        if 'name' in attrib.keys():
            at0.attrib['name']= attrib['name']
        if 'ac' in attrib.keys():
            at0.attrib['nameAc']= attrib['ac']
            
    def addFeature( self, parent, fro):
        """Adds psimi.Feature representation to parent element DOM. 
        """
        if fro is None:
            return
        
        if parent is None:
            raise MissingParentError
        
        al0 = ET.SubElement( parent, self.mif + "feature" )
        al0.attrib['id']=str(self.id)
        self.id+=1
        
        # names: shortLabel & fullName            
        self.addNames( al0, fro.label, fro.name )

        # xref: primaryRef & secondaryRef(s)
        self.addXref( al0, fro.pxref, fro.sxref)

        # featureType
        self.addCvTerm( al0, fro.type, 'featureType')

        # featureDetectionMethod        
        self.addCvTerm(al0, fro.detmth, 'featureDetectionMethod')

        # featureRangeList
        if fro.rnglst is not None and len(fro.rnglst) > 0:
            fl0 = ET.SubElement( al0, self.mif + "featureRangeList" )
            for rng in fro.rnglst: 
                fl1 = self.addFeatureRange( fl0, rng)

        # attributeList
        self.addAttList( al0, fro.attlst)

    #feature range
    def addFeatureRange(self, parent, rng):
        """Add feature range representation to parent element DOM.
        """
        fr0 = ET.SubElement( parent, self.mif + "featureRange" )
        
        #start status
        self.addCvTerm( fr0, rng['begStatus'], 'startStatus')

        #begin/begin intervel
        if 'begin' in rng.keys() and len(rng['begin']) >0:
            bg0 = ET.SubElement( fr0, self.mif + "begin" )
            bg0.attrib['position']= str(rng['begin'])
        
        if 'bint' in rng.keys() and rng['bint'] is not None:
            bg0 = ET.SubElement( fr0, self.mif + "beginInterval" )
            bg0.attrib['begin']= str(rng['bint']['begin'])
            bg0.attrib['end']= str(rng['bint']['begin'])
        
        # end status
        self.addCvTerm( fr0, rng['endStatus'], 'endStatus')
            
        #end/end interval
        if 'end' in rng.keys() and len(rng['end']) >0:
            en0 = ET.SubElement( fr0, self.mif + "end" )
            en0.attrib['position']= str(rng['end'])

        if 'eint' in rng.keys() and rng['eint'] is not None:
            en0 = ET.SubElement( fr0, self.mif + "endInterval" )
            en0.attrib['begin']= str(rng['eint']['begin'])
            en0.attrib['end']= str(rng['eint']['begin'])
            
        #isLink
        if 'link' in rng.keys() and rng['link'].lower() == 'true':
            ln0 = ET.SubElement( fr0, self.mif + "isLink" )
            ln0.text= 'true'
