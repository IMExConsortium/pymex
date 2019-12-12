import json
from lxml import etree as ET
import psimi
import math

class Dxf15Builder():
    """Builds DXF15 (ver 1.5) representation of interaction record
    as dxf <dataset>.
    """
    def __init__(self):
        self.ns="http://dip.doe-mbi.ucla.edu/services/dxf15"
        self.nsmap = {None: self.ns }
        self.dxf = "{%s}" % self.ns
        self._dom = ET.Element( self.dxf + "dataset", nsmap = self.nsmap)
        self._doc = {}
        self.id = 1

        self.pfixchar = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        
        self._dom.attrib['level']="1" 
        self._dom.attrib['version']="5"

        #self._doc['intn'] = None  # interaction node (top level) : required
        self._doc['source'] = None  # <source>           : required
        self._doc['etlst'] = None   # <experimentList>   : optional
        self._doc['irlst'] = None   # <interactorList>   : optional
        self._doc['inlst'] = None   # <interactionList>  : required 
        self._doc['aelst'] = None   # <AttributeList>    : optional


    @property
    def dom( self ):
        """Serialized (DXF 1.5) record dom
        """
        return self._dom

    @property
    def docDom( self ):
        """(DEPRECIATED) Serialized (DXF 1.5) record dom
        """
        print("dxf15builder: docDom: depreciated. Use .dom property instead.")
        return self._dom

    @property
    def docStr( self ):
        """Serialized (DXF 1.5) record representation
        """
        return str( ET.tostring(self._dom, pretty_print=True),'utf-8' )
        
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
                
    def buildInteractionRecords( self, rec, firstOnly = True ):
        """Builds dxf 1.5 representation of the interactions listed 
        in the record.
        """
        
        if not isinstance( rec, psimi.record.Record ):
            raise TypeError

        if len( rec.inlist ) > 0:
            if firstOnly: 
                self.addInteraction( self.dom, rec.inlist[0] )
            else:
                for intn in rec.inlist:
                    self.addInteraction( self.dom, intn )
        else:
            return None

    def buildInteractorRecords( self, rec, firstOnly = False ):
        """Builds dxf 1.5 representation of the interactors listed 
        in the record.
        """
        
        if not isinstance( rec, psimi.record.Record ):
            raise TypeError
       
        if len( rec.irlist ) > 0:
            if firstOnly: 
                self.addInteractor( self.dom, rec.irlist[0] )
            else:
                for intr in rec.irlist:
                    self.addInteractor( self.dom, intr )
        else:
            return None
        
        
    def addInteraction( self, parent = None, intn = None):
        """Adds psimi.Interaction representation to parent element DOM.
        """        
       
        if not isinstance( intn, psimi.interaction.Interaction ):
            raise TypeError        

        if parent is None:
            parent = self._dom
            
        in0 = ET.SubElement( parent, self.dxf + "node" )
            
        self.addType( in0,  name="link", ac="dxf:0004", ns="dxf")
        
        in0.attrib['id']= str(self.id)
        self.id+=1
        
        in0.attrib['ns']= 'dip'
        
        # find interaction dip id
        #------------------------
        # go over xrefs
                
        recAc = ""
        
        if intn.pxref['ns'] is not None and intn.pxref['ac'] is not None:        
            if intn.pxref['ns'] =='dip' and intn.pxref['refType'] == 'identity':
                recAc = intn.pxref['ac']
                
        for sxref in intn.sxref:
            if sxref['ns'] is not None and sxref['ac'] is not None: 
                if sxref['ns'] =='dip' and sxref['refType'] == 'identity':
                   recAc = sxref['ac']

        # set accession
        #--------------
        
        in0.attrib['ac'] = recAc
        
        # names: label & name
        #--------------------
        
        self.addNames( in0, intn.label, intn.name )


        # set xref list
        #--------------
        
        xrlist = None
        
        if intn.pxref is not None or (intn.sxref is not None and len(intn.sxref) > 0) :
        
            xrlist = self.addXrefList( in0 )
            self.addXref( xrlist, pxref=intn.pxref, sxref=intn.sxref)
            
        # set attributes
        #----------------
        
        # * link type as attribute
        
        
        atlist = None
        
        if intn.type is not None:
            atlist = ET.SubElement( in0, self.dxf + "attrList" )        
            self.addAttr( atlist, name='link-type', ns='dip', ac='dip:0001',
                          value = intn.type )

            #<ns2:attr name="link-type" ac="dip:0001" ns="dip">
            #<ns2:value ac="MI:0914" ns="psi-mi">association</ns2:value>
            #</ns2:attr>

        # * other attributes
  
        if intn.attlist is not None and len(intn.attlist) > 0:       
            if atlist is None:
                atlist = ET.SubElement( in0, self.dxf + "attrList" )
            self.addAttrList(atlist, intn.attlist )
                    
        #<modelled>false</modelled>   ???
        #<intraMolecular>false</intraMolecular>  ???
        #<negative>false</negative>   ??? 
        
        # participants (as part list)
        #----------------------------
        
        if intn.ptolist is not None and len(intn.ptolist) > 0:
             pl0 = ET.SubElement( in0, self.dxf + "partList" )

             pfix = 'A'
             
             for part in intn.ptolist:  
                 self.addParticipant( pl0, part, postfix = pfix  )
                 pfix = self.nextPfix( pfix )

        # experiment(s)
        #--------------
        
        #  <ns2:xref type="supported-by" typeAc="dxf:0008" typeNs="dxf"
        #            ac="DIP-3102X" ns="dip">

        if intn.evolist is not None and len(intn.evolist) > 0:
            if xrlist is None:            
                xrlist = self.addXrefList( in0 )            
            
            for evo in intn.evolist:
                evx0 = ET.SubElement( xrlist, self.dxf + "xref" ) 
                evx0.attrib['type']="supported-by"
                evx0.attrib['typeNs']="dxf"
                evx0.attrib['typeAc']="dxf:0008"
                evx0.attrib['ns']='dip'

                evoAc = ''
                if evo.pxref['ns']=='dip' and evo.pxref['refType']=='identity':
                    evoAc = evo.pxref['ac']
                if ( evoAc is None or len(evoAc)==0 ) and evo.sxref is not None:        
                    for sxr in evo.sxref:
                        if sxr['ns']=='dip' and sxr['refType']=='identity': 
                            evoAc = sxr['ac']    
                evx0.attrib['ac'] = evoAc
                        
                self.addExperiment( evx0, evo, ns='dip', ac=evoAc)

                
    def addExperiment( self, parent, evid, ns = None , ac = None ):
        """Adds psimi.Experiment representation to parent element DOM.
        """
        if not isinstance(evid, psimi.evidence.Evidence):
            raise TypeError

        # only simple evidence supported
        nexp = psimi.Experiment.fromEvidence( evid )
        
        ev0 = ET.SubElement( parent, self.dxf + "node" )        
        ev0.attrib['id']= str(self.id)
        self.id+=1

        if ns is not None and ac is not None:
            ev0.attrib['ns'] = ns
            ev0.attrib['ac'] = ac
        else:
            ev0.attrib['ns'] = 'dip'
            ev0.attrib['ac'] = ''

            evAc = ''
            if evid.pxref['ns'] == 'dip' and evid.pxref['refType'] == 'identity':
                evAc = evid.pxref['ac']
            if (evAc is None or len(evAc) == 0) and evid.sxref is not None:
                for sxr in evid.sxref:
                    if sxr['ns'] == 'dip' and sxr['refType'] == 'identity': 
                        evAc = sxr['ac']
                    
            ev0.attrib['ac'] = evAc

        self.addType(ev0, name="evidence", ac="dxf:0015", ns="dxf")

        # names
        #------
        
        self.addNames( ev0, nexp.label, nexp.name )

        # xrefs
        #------
        
        xrlist  = None

        # * evidence pmid as xref
        
        if evid.pmid is not None:
            if xrlist is None: 
                xrlist = ET.SubElement( ev0, self.dxf + "xrefList" ) 
            
            #<ns2:xref type="described-by" typeAc="dxf:0014" typeNs="dxf"
            #          ac="9832501" ns="PubMed"/>
            
            xr0 = ET.SubElement( xrlist, self.dxf + "xref" ) 
            xr0.attrib['type'] = 'described-by'
            xr0.attrib['typeNs'] = 'dxf'
            xr0.attrib['typeAc'] = 'dxf:0014'
            xr0.attrib['ns'] = 'PubMed'
            xr0.attrib['ac'] = evid.pmid
                      
        # * other xrefs
        
        self.addXref( xrlist, nexp.pxref, nexp.sxref)
                
        # attributes
        #-----------

        attlist = None
        
        # link-type

        # from parent ???
           
        # interaction detection method
        #-----------------------------
        
        if nexp.intMth is not None:
            if attlist is None:
                attlist = ET.SubElement( ev0, self.dxf + "attrList" )

            self.addAttr( attlist, ac='MI:0001', ns='psi-mi',
                          name = 'interaction detection method',
                          value = nexp.intMth )

        # participant identification method
        #----------------------------------
        
        if nexp.prtMth is not None:
            if attlist is None:
                attlist = ET.SubElement( ev0, self.dxf + "attrList" )

            self.addAttr( attlist, ac='MI:0002', ns='psi-mi',
                          name = 'participant identification method',
                          value = nexp.prtMth )

        # host organism list
        #-------------------
    
        if nexp.ehost is not None:
            if attlist is None:
                attlist = ET.SubElement( ev0, self.dxf + "attrList" )
            
            for ho in nexp.ehost:
                self.addAttr( attlist, ac='dxf:0066', ns='dxf',
                                  name = 'experiment host',
                                  value = ho )
                                               
        # other attributes
        #-----------------
        self.addAllAttr(attlist, nexp.attrib )
        
    def addParticipant( self, parent, prt, postfix = '' ):
        """Adds psimi.Participant representation to parent element DOM.
        """       
        if not isinstance(prt, psimi.participant.Participant):
            raise TypeError

        if parent is None:
            raise MissingParentError
        
        pa0 = ET.SubElement( parent, self.dxf + "part" )
        pa0.attrib['id']= str(self.id)
        self.id+=1
        pa0.attrib['name']= ''
        self.addType(pa0, name="linked-node", ac="dxf:0010", ns="dxf")
                
        # names
        #------

        label = None
        
        if prt.label == 'N/A':
            label = None
        else:
            label = prt.label

        if label is None or len(label) == 0:
            label = prt.interactor.label
            if label is None or len(label) == 0:
                label = prt.interactor.name

        if label == None:
            label = ''

        pa0.attrib['name'] = label + "{" + postfix + "}"
            
        # xref: primaryRef & secondaryRef(s)
        #self.addXref( pa0, prt.pxref, prt.sxref)

        #interactor
        #----------
        self.addInteractor( pa0, prt.interactor)
        
        #participantIdentificationMethodList
        #   participantIdentificationMethod
        #if prt.pidmth is not None and len(prt.pidmth) > 0:
        #    pa1 = ET.SubElement( pa0, self.dxf + "participantIdentificationMethodList" )
        #    for pim in prt.pidmth:
        #        pa2 = self.addCvTerm( pa1, pim, ename='participantIdentificationMethod')
                
        #biological role
        #if prt.brole is not None:
        #    br0 = self.addCvTerm( pa0, prt.brole, ename='biologicalRole')
        
        #experimentalRoleList
        #   experimentalRole
        #if prt.erole is not None and len(prt.erole) > 0:
        #    ex0 = ET.SubElement( pa0, self.dxf + "experimentalRoleList" )
        #    for ero in prt.erole:
        #        ero1 = self.addCvTerm( ex0, ero, ename='experimentalRole')
                    
        #experimentalPreparationList
        #   experimentalPreparation
        #if prt.eprep is not None and len(prt.eprep) > 0:
        #    ep0 = ET.SubElement( pa0, self.dxf + "experimentalPreparationList" )
        #    for epo in prt.eprep:
        #        ep1 = self.addCvTerm( ep0, epo, ename='experimentalPreparation')
                        
        #featureList
        #  feature
        #if prt.frolst is not None:
        #    fr0 = ET.SubElement( pa0, self.dxf + "featureList" )
        #    for fro in prt.frolst:
        #        fr1 = self.addFeature( fr0, fro )
        
        #hostOrganismList      
        #  hostOrganism
        #if prt.ehost is not None:
        #    hol = ET.SubElement( pa0, self.dxf + "hostOrganismList" )
        #    for ho in prt.ehost:
        #        self.addOrganism( hol, ho, ename='hostOrganism')
     
        #attributeList
        #self.addAttList(pa0, prt.attrib )

        
    def addInteractor( self, parent = None,  node = None, id=None ):
        
        if not isinstance(node, psimi.interactor.Interactor):
            raise TypeError

        if parent is None:
            parent = self._dom
        
        ir0 = ET.SubElement( parent, self.dxf + "node" )
        ir0.attrib['id']= str(self.id)
        self.id+=1

        ir0.attrib['ns'] = 'dip'
        
        self.addType( ir0, node.type['ns'],
                      node.type['ac'], node.type['label'])
        
        lb0 = ET.SubElement( ir0, self.dxf + "label" )
        lb0.text=node.label

        if node.name is not None and len(node.name) > 0:
            nm0 = ET.SubElement( ir0, self.dxf + "name" )
            nm0.text=node.name

        xrl = None
            
        # organism
        #---------
        if node.species is not None:            
            if xrl is None:
                xrl = ET.SubElement( ir0, self.dxf + "xrefList" ) 
            sx0 = ET.SubElement( xrl, self.dxf + "xref" ) 
            sx0.attrib['type']='produced-by'
            sx0.attrib['typeNs']='dxf'
            sx0.attrib['typeAc']='dxf:0007'
            sx0.attrib['ns']=node.species['ns']
            sx0.attrib['ac']=node.species['ac']

            self.addSpecies( sx0, node.species['ac'],
                             node.species['label'], node.species['name'] )

        inrAc = ""
        
        if node.pxref['ns'] is not None and node.pxref['ac'] is not None:        
            if node.pxref['ns'] =='dip':
                px = node.pxref
                if 'refType' not in px.keys() or px['refType']=='identity':
                    inrAc = px['ac']

        for sx in node.sxref:
            if sx['ns'] is not None and sx['ac'] is not None:                
                if sx['ns'] =='dip':
                    if 'refType' not in sx.keys() or sx['refType']=='identity':
                        inrAc = sx['ac']

        ir0.attrib['ac'] = inrAc
                    
        # xref: primaryRef & secondaryRef(s)
        #-----------------------------------
        
        if node.pxref is not None or ( node.sxref is not None
                                       and len(node.sxref) > 0 ):
            if xrl is None:
                xrl = ET.SubElement( ir0, self.dxf + "xrefList" ) 
            
            self.addXref( xrl, node.pxref, node.sxref)

        # attributes
        #-----------
        attlist = None
        
        if node.sequence is not None:
            if attlist is None:
                attlist = ET.SubElement( ir0, self.dxf + "attrList" )
            
            self.addAttr( attlist, ac='dip:0008', ns='dip',
                          name = 'sequence',
                          value = {'value': node.sequence} )
            

    #---------------------------------------------------------------------------
                        
    def addSource( self, src):
        """Add psimi.Source representation.
        """
        if not isinstance(src, psimi.source.Source):
            raise TypeError
        # names
        if self._doc['source']  is None:
            self._doc['source'] = ET.SubElement( self._doc['entry'],
                                                self.dxf + "source" )
        self.addNames( self._doc['source'], src.label, src.name )

        # bibref
        if src.bibref is not None:
            #print(src.bibref)
            self.addBibref(  self._doc['source'], src.bibref )

        # xref
        self.addXref( self._doc['source'], src.pxref, src.sxref)

        #attribute
        self.addAttList(self._doc['source'], src.attlst )
                        
    def addBibref( self, parent, bibref=None ):
        """Add bibref representation to parent element DOM.
        """
        if bibref is None: 
            return

        br0 = ET.SubElement( parent, self.dxf + "bibref" )
        
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

        ir0 = ET.SubElement( parent, self.dxf + ename )
        ir0.attrib['ncbiTaxId']= organism['ac']
        ir1 = ET.SubElement( ir0, self.dxf + "names" )
        if 'label' in organism.keys():
            ir2 = ET.SubElement( ir1, self.dxf + "shortLabel" )
            ir2.text = organism['label']

        if 'name' in organism.keys():
            ir3 = ET.SubElement( ir1, self.dxf + "fullName" )
            ir3.text = organism['name']

        if 'ctype' in organism.keys():
            ir4 = ET.SubElement( ir1, self.dxf + "cellType" )
            ctype = organism['ctype']
            if 'label' in ctype.keys():
                label = ctype['label']
            if 'name' in ctype.keys():
                name = ctype['name']
            if label is not None or name is not None:
                ir5 = ET.SubElement( ir4, self.dxf + "names" )
                if label is not None:
                    ir6 = ET.SubElement( ir5, self.dxf + "shortLabel" )
                    ir6.text=label
                if name is not None:
                    ir7 = ET.SubElement( ir5, self.dxf + "fullName" )
                    ir7.text=name

            if 'pxref' in ctype.keys():
                pxref = ctype['pxref']
                
            if 'sxref' in ctype.keys():
                sxref = ctype['sxref']

            if pxref is not None or sxref is not None:                
                self.addXref( ir4, pxref, sxref )
                
    def addNames( self, parent, label=None, name=None ):
        """Add label (and name) representation to parent element DOM.
        """

        if parent is None:
            raise MissingParentError

        la0 = ET.SubElement( parent, self.dxf + "label" )
        if label is not None:            
            la0.text = label
        else:
            if name is not None:
                la0.text = name
                
        if name is not None and name != label:
            na0 = ET.SubElement( parent, self.dxf + "name" )
            na0.text = name

    def addCvTerm( self, parent, term = None, ename=None):
        """Add CV term representation to parent element DOM.
        """
        if ename is None or term is None:
            return

        if parent is None:
            raise MissingParentError
        
        #{'nsAc': 'MI:0488', 'name': 'x-ray diffraction',
        # 'label': 'x-ray diffraction', 'ac': 'MI:0114', 'ns': 'psi-mi'}
        
        cv0 = ET.SubElement( parent, self.dxf + ename )
        cv1 = ET.SubElement( cv0, self.dxf + "names" )

        if 'label' in term.keys():
            cv2 = ET.SubElement( cv1, self.dxf + "shortLabel" )
            cv2.text = term['label']

        if 'name' in term.keys():
            cv2 = ET.SubElement( cv1, self.dxf + "fullName" )
            cv2.text = term['name']

        pxref = term.copy() # shallow copy, add ref type info when missing
            
        if 'refType' not in pxref.keys():                
            pxref['refType']="identity"
            
        if 'refTypeAc' not in pxref.keys():
            pxref['refTypeAc'] = "MI:0356"
            
        self.addXref( cv0, pxref )
        
    def addFeature( self, parent, fro):
        """Adds psimi.Feature representation to parent element DOM. 
        """
        if fro is None:
            return
        
        if parent is None:
            raise MissingParentError
        
        al0 = ET.SubElement( parent, self.dxf + "feature" )
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
            fl0 = ET.SubElement( al0, self.dxf + "featureRangeList" )
            for rng in fro.rnglst: 
                fl1 = self.addFeatureRange( fl0, rng)

        # attributeList
        self.addAttList( al0, fro.attlst)

    #feature range
    def addFeatureRange(self, parent, rng):
        """Add feature range representation to parent element DOM.
        """
        fr0 = ET.SubElement( parent, self.dxf + "featureRange" )
        
        #start status
        self.addCvTerm( fr0, rng['begStatus'], 'startStatus')

        #begin/begin intervel
        if 'begin' in rng.keys() and len(rng['begin']) >0:
            bg0 = ET.SubElement( fr0, self.dxf + "begin" )
            bg0.attrib['position']= str(rng['begin'])
        
        if 'bint' in rng.keys() and rng['bint'] is not None:
            bg0 = ET.SubElement( fr0, self.dxf + "beginInterval" )
            bg0.attrib['begin']= str(rng['bint']['begin'])
            bg0.attrib['end']= str(rng['bint']['begin'])
        
        # end status
        self.addCvTerm( fr0, rng['endStatus'], 'endStatus')
            
        #end/end interval
        if 'end' in rng.keys() and len(rng['end']) >0:
            en0 = ET.SubElement( fr0, self.dxf + "end" )
            en0.attrib['position']= str(rng['end'])

        if 'eint' in rng.keys() and rng['eint'] is not None:
            en0 = ET.SubElement( fr0, self.dxf + "endInterval" )
            en0.attrib['begin']= str(rng['bint']['begin'])
            en0.attrib['end']= str(rng['bint']['begin'])
            
        #isLink
        if 'link' in rng.keys() and rng['link'].lower() == 'true':
            ln0 = ET.SubElement( fr0, self.dxf + "isLink" )
            ln0.text= 'true'

            
    #---------------------------------------------------------------------------        
    # attribute list    
    #---------------
    
    def addAttrList( self, parent, attrList = None):
        """Add attribute list representation to parent element DOM.
        """
        
        al0 = ET.SubElement( parent, self.dxf + "attrList" )
        return self.addAllAttr( al0, attrList)
        
    
    def addAllAttr( self, parent, attrList = None):
        """Add all attributes to parent element DOM.
        """
        if attrList is None:
            return None

        for attr in attrList:
            ns = None 
            ac = None
            name = None
            value = None
            
            if 'ac' in attr:
                ac = attr['ac']
                
            if 'ns' in attr:
                ns = attr['ns']
            else:
                if ac is not None:
                    if ac.startswith('MI:'):
                        ns = 'psi-mi'
                    if ac.startswith('dxf:'):
                        ns = 'dxf'
                    if ac.startswith('dip:'):
                        ns = 'dip'

            if 'name' in attr:
                    name = attr['name']
                    
            if 'value' in attr:
                value = attr['value']
                
            self.addAttr( parent, name, ns, ac, { 'name': value })
            return parent
            
    def addAttr( self, parent, name, ns, ac, value ):
        """Add attribute representation to parent element DOM. 
        """
                
        at0 = ET.SubElement( parent, self.dxf + "attr" )
        if  name is not None:
            at0.attrib['name'] = name
        if ns is not None:
            at0.attrib['ns'] = ns
        if ac is not None:
            at0.attrib['ac'] = ac

            if ns is None:
                if ac.startswith('MI:'):
                    at0.attrib['ns'] = 'psi-mi'
                if ac.startswith('dxf:'):
                    at0.attrib['ns'] = 'dxf'
                if ac.startswith('dip:'):
                    at0.attrib['ns'] = 'dip'
                 
        if value is not None:            
            av0 = ET.SubElement( at0, self.dxf + "value" )
            if 'label' in value and value['label'] is not None:
                av0.text= value['label']
            else:
                if 'name' in value and value['name'] is not None:
                    av0.text= value['name']
                if 'value' in value and value['value'] is not None:
                    av0.text= value['value']
                    
            if 'ns' in value and value['ns'] is not None:
                av0.attrib['ns']= value['ns']
            if 'ac' in value and value['ac'] is not None:
                av0.attrib['ac']= value['ac']
            
                if 'ns' not in value:
                    if value['ac'].startswith('MI:'):
                        av0.attrib['ns'] = 'psi-mi'
                    if value['ac'].startswith('dxf:'):
                        av0.attrib['ns'] = 'dxf'
                    if value['ac'].startswith('dip:'):
                        av0.attrib['ns'] = 'dip'

                        
    def getXref(self, obj, type='', ns=''):
        acl = []        
        if obj.pxref is not None:
            x = obj.pxref
            if x['ns'] == ns and x['refType']==type:
                acl.append( x['ac'])

        if obj.sxref is not None:
            for x in obj.sxref:                
                if x['ns'] == ns and x['refType']==type:
                    acl.append( x['ac'])        
        return acl

    #---------------------------------------------------------------------------
    # xref list    
    #-----------
    
    def addXrefList( self, parent, xrefList = None):
        """Add xref list representation to parent element DOM.
        """
        
        al0 = ET.SubElement( parent, self.dxf + "xrefList" )
        self.addAllXref( al0, xrefList)
        return al0
    
    def addAllXref( self, parent, xrefList = None):
        """Add all xrefs to parent element DOM.
        """
        if xrefList is None:
            return None

        for xref in xrefList:
            self.addXref( parent, xref.pxref, xref.sxref)

        
    def addXref( self, parent, pxref=None, sxref=None):
        """Add cross references to parent element DOM.
        """

        # dxf:0009 identical-to
        
        imexId = None
        
        #{'ver': 'SP_26', 'ns': 'uniprotkb', 'ac': 'P0AE67', 'nsAc': 'MI:0486'}

        #{'ac': '1EAY', 'ns': 'wwpdb', 'nsAc': 'MI:0805',
        #'refTypeAc': 'MI:0356', 'refType': 'identity' }
        
        #<secondaryRef id="IM-26977-1" db="imex" dbAc="MI:0670"
        #          refType="imex-primary" refTypeAc="MI:0662"/>

        #<ns2:xref type="supports" typeAc="dxf:0013" typeNs="dxf"
        #          ac="DIP-2612E" ns="dip"/>
            
        if pxref is not None:

            if isinstance(pxref, list):
                pxref = pxref[0]

            ir1 = ET.SubElement( parent, self.dxf + "xref" )

            if 'ac' in pxref.keys():
                if 'ver' in pxref.keys():
                    ir1.attrib['ac']=pxref['ac'] + "." + pxref['ver']
                else:
                    ir1.attrib['ac']=pxref['ac']

                if 'ns' in pxref.keys():
                    ir1.attrib['ns']=pxref['ns']
                    
            if 'refType' in pxref.keys():
                ir1.attrib['type']=pxref['refType']

            if 'refTypeAc' in pxref.keys() and len(pxref['refTypeAc']) > 0:
                ir1.attrib['typeAc']=pxref['refTypeAc']
                if pxref['refTypeAc'].startswith('MI:'):
                    ir1.attrib['typeNs'] = 'psi-mi'
                elif pxref['refTypeAc'].startswith('dxf:'):
                    ir1.attrib['typeNs'] = 'dxf'
                elif pxref['refTypeAc'].startswith('dip:'):
                    ir1.attrib['typeNs'] = 'dip'
                    
            if 'ns' in pxref.keys() and 'ac' in pxref.keys() and 'refType' in pxref.keys():
                if pxref['ns'] == 'imex' and pxref['refType'] == 'imex-primary':
                    imexId = pxref['ac']

            if 'ns' in pxref.keys() and 'ac' in pxref.keys() and 'refType' not in pxref.keys():
                if pxref['ns'] == 'dip' and pxref['ac'] is not None and len( pxref['ac']) > 0:
                    ir1.attrib['type']='identity'
                    ir1.attrib['typeNs']='psi-mi'
                    ir1.attrib['typeAc']='MI:0356'

            if 'typeNs' not in ir1.attrib or 'typeAc' not in ir1.attrib:
                ir1.attrib['typeNs'] = 'dxf'
                ir1.attrib['typeAc'] = 'dxf:0018'
                ir1.attrib['type'] = 'related-to'


            # psi-mi identity => dxf identical-to 
            
            if ir1.attrib['typeNs']== 'psi-mi' and ir1.attrib['typeAc'] == 'MI:0356':
                ir1.attrib['typeNs'] = 'dxf'
                ir1.attrib['typeAc'] = 'dxf:0009'
                ir1.attrib['type'] = 'identical-to'

                
            if sxref is not None and len(sxref) > 0:


                for sxr in sxref:
                    ir1 = ET.SubElement( parent, self.dxf + "xref" )
                    if 'ac' in sxr.keys():
                        if 'ver' in sxr.keys():
                            ir1.attrib['ac']=sxr['ac'] + "." + sxr['ver']
                        else:
                            ir1.attrib['ac']=sxr['ac']

                    if 'ns' in sxr.keys():
                        ir1.attrib['ns']=sxr['ns']

                    if 'refType' in sxr.keys():
                        ir1.attrib['type']=sxr['refType']

                    if 'refTypeAc' in sxr.keys():
                        ir1.attrib['typeAc']=sxr['refTypeAc']
                        if sxr['refTypeAc'].startswith('MI:'):
                            ir1.attrib['typeNs'] = 'psi-mi'
                        elif sxr['refTypeAc'].startswith('dxf:'):
                            ir1.attrib['typeNs'] = 'dxf'
                        elif sxr['refTypeAc'].startswith('dip:'):
                            ir1.attrib['typeNs'] = 'dip'
                            
                    if 'ns' in sxr.keys() and 'ac' in sxr.keys() and 'refType' in sxr.keys():
                        if sxr['ns'] == 'imex' and sxr['refType'] == 'imex-primary':
                            imexId = sxr['ac']
                    
                    if 'ns' in sxr.keys() and 'ac' in sxr.keys() and 'refType' not in sxr.keys():
                        if sxr['ns'] == 'dip' and sxr['ac'] is not None and len( sxr['ac']) > 0:
                            ir1.attrib['refType']='identity'
                            ir1.attrib['refTypeAc']='MI:0356'

                    if 'typeNs' not in ir1.attrib or 'typeAc' not in ir1.attrib:
                        ir1.attrib['typeNs'] = 'dxf'
                        ir1.attrib['typeAc'] = 'dxf:0018'
                        ir1.attrib['type'] = 'related-to'

                    if ir1.attrib['typeNs']== 'psi-mi' and ir1.attrib['typeAc'] == 'MI:0356':                    
                        ir1.attrib['typeNs'] = 'dxf'
                        ir1.attrib['typeAc'] = 'dxf:0009'
                        ir1.attrib['type'] = 'identical-to'

                            
            #return ir0
        #else:
            # return None
        return imexId

    
    def addType(self, parent, ns, ac, name):
        tp0 = ET.SubElement( parent, self.dxf + "type" )
        tp0.attrib['ns']= ns
        tp0.attrib['ac']= ac
        tp0.attrib['name']=name

    
    def addPart( self, parent, node = None, name = ''):
        pt0 = ET.SubElement( parent, self.dxf + "part" )
        pt0.attrib['id']=str(self.id)
        self.id+=1
        pt0.attrib['name']=name
        #<ns2:part id="3" name="CEG1{A}">
        # <ns2:type name="linked-node" ac="dxf:0010" ns="dxf"/>
        # <ns2:node ac="DIP-2298N" ns="dip" id="2">
                             
        tp0 = ET.SubElement( pt0, self.dxf + "type" )
        tp0.attrib['ns']='dxf'
        tp0.attrib['ac']='dxf:0010'
        tp0.attrib['name']='linked-node'
        
        if node is not None:
            if isinstance( node, psimi.interactor.Interactor ):
                self.addInteractor(pt0, node=node)
        


    def addSpecies( self, parent, taxid, label, name):
        sp0 = ET.SubElement( parent, self.dxf + "node" )
        sp0.attrib['id'] = str(self.id)
        self.id+=1
        sp0.attrib['ns'] = 'taxid'
        sp0.attrib['ac'] = taxid
        self.addType( sp0, 'dxf','dxf:0301', 'organism')
        sl0=ET.SubElement( sp0, self.dxf + "label" )
        sl0.text = label
        sn0=ET.SubElement( sp0, self.dxf + "name" )
        sn0.text = name
        
        
    def nextPfix( self, pfix ):
        #
        radix = len(self.pfixchar)
        
        val = 0
        pos = 0 
        for d in pfix[::-1]:            
            val += math.pow(radix, pos)*self.pfixchar.find(d)
            pos +=1
        cval = val + 1
        nfix = ''
        while cval >= radix:
            mod = int(cval % radix)
            d = self.pfixchar[mod]
            cval = (cval - mod)/radix
            nfix = d + nfix                

        d = self.pfixchar[int(cval)]
        nfix = d + nfix

        return nfix
        
