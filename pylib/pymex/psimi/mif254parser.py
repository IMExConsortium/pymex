import json
from lxml import etree as ET
from pymex.psimi import record as MIF

class Mif254Parser():
    """MIF 254 interaction record parser.
    """
    def __init__( self ):
        self.ns = { 'mif': 'http://psi.hupo.org/mi/mif' }

    def parse( self, source ):
        """Returns psimi.Record representation of the first <entry> element
        of the source PSI-MI XML (v2.5.4) file.
        """
        mif = {}
        #mif["entry"] = {}
        mif["source"] = {} # source
        mif["dom"] = {}    # DOM
        mif["i10r"] = {}   # interactors
        mif["e10t"] = {}   # experiments 
        mif["i11n"] = {}   # interactions
        
        parser = ET.XMLParser( remove_blank_text=True ) 
        dom = ET.parse( source, parser )

        #print(ET.tostring(dom))
        
        mif['dom']['doc'] = dom
        elist = dom.xpath( '//mif:entry', namespaces = self.ns)        
        entry = elist[0]

        # parse source
        mif["source"] = self.__parseSource( entry )        
        mif["source"]["root"] = mif
        
        # parse experiments
        expl = entry.xpath( ".//mif:experimentDescription",
                            namespaces = self.ns )

        for cexp in expl:
            e10t = self.__parseExperiment( cexp )
            e10t["root"] = mif

            mif["e10t"][ e10t['rid'] ] = e10t              
      
        # parse interactors 
        i10rl = entry.xpath( ".//mif:interactor", namespaces = self.ns )            
        for cintr in i10rl:
            ii = self.__parseInteractor( cintr )
            ii["root"] = mif

            mif["i10r"][ii['rid']] = ii
            
        # parse interactions
        i11nl = entry.xpath( ".//mif:interaction", namespaces = self.ns )
        for cintn in i11nl:        
            ii = self.__parseInteraction( mif, cintn )
            ii["root"] = mif

            mif["i11n"][ii['rid'] ] = ii
                        
        return MIF.Record( mif )
 
    # private methods
    #---------------------------------------------------------------------------            

    def __parseInteraction( self, mif, dom ):
        i11n = {}
        i11n['dom'] = dom
        refID =  dom.xpath( "./@id", namespaces = self.ns )[0]        
        i11n['rid'] = refID

        imexID =  dom.xpath( "./@imexId", namespaces = self.ns )
        if imexID:
            i11n['imex'] = imexID[0]
        else:
            i11n['imex'] = ""

        SL =  dom.xpath( "./mif:names/mif:shortLabel/text()",
                         namespaces = self.ns )
        if len(SL) > 0:
            i11n[ 'label' ] = SL[0]
        else:
            i11n[ 'label' ] = None

            
        FN =  dom.xpath( "./mif:names/mif:fullName/text()",
                         namespaces = self.ns )
        if len( FN ) > 0:
            i11n[ 'name' ] = FN[0]
        else:
            i11n[ 'name' ] = None

        # xrefs
        xrefDom = dom.xpath( "./mif:xref", namespaces = self.ns )
        if xrefDom:
            (i11n['pxref'], i11n['sxref']) = self.__parseXref( xrefDom[0] )        
            
        # participant list
        p11tl = dom.xpath( "./mif:participantList/mif:participant",
                           namespaces = self.ns )
        p11t = []
        for p in p11tl:
            p11t.append( self.__parseParticipant( mif, p ) )
            
        i11n['p11t'] = p11t

        # experiment ref list
        e10tl = dom.xpath( "./mif:experimentList", namespaces = self.ns )[0]
    
        e10t = []
        evl = []

        i11n["e10t"] = e10t  # experiments as in mif
        i11n["evid"] = evl   # evidence (one for each experiemnt)
        
        for e in e10tl:
            obslst = []
            evid = {'etype': {'ns':'eco',
                              'ac':'eco:0000006',
                              'name':'experimental evidence'},
                    'obslst': obslst }
            
            if e.xpath('local-name(.)') == 'experimentRef':                
                et = mif["e10t"][ e.xpath('./text()')[0] ]
                
                e10t.append( et )
                obslst.append( et )                
            else:

                et = self.__parseExperiment( e )
                et['dom'] = e
                e10t.append( et )
                obslst.append( et )

            evl.append(evid)
                              
        # interaction type
        itype = self.__parseCV( dom.xpath( ".//mif:interactionType",
                                           namespaces = self.ns )[0] )
                                
        i11n["itype"] = itype

        #<modelled>false</modelled>
        mdlst = dom.xpath( "./mif:modelled/text()", namespaces = self.ns )
        if len(mdlst) > 0: 
            i11n["modelled"] = mdlst[0]
            
            
        #<intraMolecular>false</intraMolecular>
        imlst = dom.xpath( "./mif:intraMolecular/text()",
                           namespaces = self.ns )
        if len(imlst) > 0: 
            i11n["intramol"] = imlst[0]
            
            
        #<negative>false</negative>
        nelst = dom.xpath( "./mif:negative/text()", namespaces = self.ns )
        if len(nelst) > 0: 
            i11n["negative"] = nelst[0]
        
        attlistDom = dom.xpath( "./mif:attributeList", namespaces = self.ns )
    
        if attlistDom:
            i11n['attList'] = self.__parseAtt( attlistDom[0] )
        
        return i11n
            

    def __parseParticipant( self, mif, dom ):    

        p11t = {}
        p11t['dom']=dom
        
        refID =  dom.xpath( "./@id",
                            namespaces = self.ns )[0]
        # names: 
        SL =  dom.xpath( "./mif:names/mif:shortLabel/text()",
                          namespaces = self.ns )
        if len(SL) > 0:
            p11t[ 'label' ] = SL[0]
        else:
            p11t[ 'label' ] = None
            
        FN =  dom.xpath( "./mif:names/mif:fullName/text()",
                         namespaces = self.ns )
        if len( FN ) > 0:
            p11t[ 'name' ] = FN[0]
        else:
            p11t[ 'name' ] = None
        
        # interactor
        iref = dom.xpath( "./mif:interactorRef/text()",
                          namespaces = self.ns )

        if len( iref ) == 1:
            iref = iref[0]
            p11t['iref'] = iref
            p11t['i10r'] = mif["i10r"][iref]
        else:
            p11t['iref'] = None
            
        if p11t['iref'] is None:
            i10rl = dom.xpath( ".//mif:interactor", namespaces = self.ns )
            if i10rl:
                p11t['i10r'] =  self.__parseInteractor( i10rl[0] )

        # participant ident method
        pimlst = dom.xpath( ".//mif:participantIdentificationMethod",
                            namespaces = self.ns )

        p11t['pidmth'] = []
        for pim in pimlst:
            p11t['pidmth'].append( self.__parseCV( pim ) )

        # bio role
        #print("XXXX>")
        #print(ET.tostring(dom))
        bioRoleDom = dom.xpath( "./mif:biologicalRole", namespaces = self.ns )
        #print(bioRoleDom)
        #print("<XXXX")
        if bioRoleDom is not None and len(bioRoleDom) >0:
            p11t['brole'] = self.__parseCV( bioRoleDom[0] ) 
    
        # exp role
        erlst = dom.xpath( ".//mif:experimentalRole", namespaces = self.ns )
        p11t['erole'] = []
        for er in erlst:
            p11t['erole'].append( self.__parseCV( er ))
                     
        # exp prep role
        eprlst = dom.xpath( ".//mif:experimentalPreparation",
                            namespaces = self.ns )

        p11t['eprep'] = []
        for epr in eprlst:
            p11t['eprep'].append( self.__parseCV( epr ) )

        # exp host
        
        #<hostOrganismList>
        # <hostOrganism ncbiTaxId="83333">
        #  <names>
        #   <shortLabel>ecoli</shortLabel>
        #   <fullName>Escherichia coli (strain K12)</fullName>
        #  </names>
        # </hostOrganism>
        #</hostOrganismList>
                
        ehost = dom.xpath( ".//mif:hostOrganism", namespaces = self.ns )
        if ehost:
            p11t['ehost'] = []
            for eh in ehost:            
                p11t['ehost'].append( self.__parseHost( eh ))
                                
        # features
        ftrDom = dom.xpath( ".//mif:feature", namespaces = self.ns )        
        p11t['feature'] = self.__parseFeature( ftrDom )
        
        attDom = dom.xpath( "./mif:attributeList", namespaces = self.ns )
        if attDom:
            p11t['attrib'] = self.__parseAtt( attDom[0] )            
        else:
            p11t['attrib'] = None
        return p11t

    def __parseFeature( self, dom ):

        ftrl = []
    
        for f in dom:

            ftr = {}
            
            ftrSL = f.xpath( "./mif:names/mif:shortLabel/text()",
                             namespaces = self.ns )
            if ftrSL:
                ftr['label'] = ftrSL[0]
            else:
                ftr['label'] = None
                
            ftrFN =  f.xpath( "./mif:names/mif:fullName/text()",
                               namespaces = self.ns )
            if ftrFN:
                ftr['name'] = ftrFN[0] 
            else:
                ftr['name'] = None
                
            # feature type
            
            ftrTPDom = f.xpath( "./mif:featureType",
                                  namespaces = self.ns )
            
            ftr['type'] = self.__parseCV( ftrTPDom[0] )

            # feature det method
            
            ftrDMDom = f.xpath( "./mif:featureDetectionMethod",
                                  namespaces = self.ns )
            if len( ftrDMDom ) > 0:
                ftr['detmth'] = self.__parseCV( ftrDMDom[0] )
            else:
                ftr['detmth'] = None

            # feature range(s)
            ftrRGDom = f.xpath( ".//mif:featureRange",
                                  namespaces = self.ns )                        
            ftr['rnglst'] = self.__parseRange( ftrRGDom )
            ftrl.append(ftr)


            # attribute list
            attlistDom = f.xpath( "./mif:attributeList",
                                  namespaces = self.ns )

            if attlistDom:
                ftr['attrib'] = self.__parseAtt( attlistDom[0] )            
            else:
                ftr['attrib'] = None
            
        return ftrl
                  
    def __parseRange( self, dom ):

        rng = []

        for r in dom:            
            crng = {}

            sSTDom = r.xpath( "./mif:startStatus", namespaces = self.ns )            
            sST = self.__parseCV(  sSTDom[0])
            crng["begStatus"] = sST

            sPS = r.xpath( "./mif:begin/@position", namespaces = self.ns )
            if sPS:
                crng["begin"] = sPS[0]

            sPSI = r.xpath( "./mif:beginInterval", namespaces = self.ns )
            if sPSI:

                sPSIbegin = sPSI[0].xpath( "./@begin", namespaces = self.ns )
                sPSIend = sPSI[0].xpath( "./@end", namespaces = self.ns )

                if sPSIbegin and sPSIend:
                    crng["bint"] = {'begin':sPSIbegin[0], 'end':sPSIend[0]}
                
            eSTDom = r.xpath( "./mif:endStatus",namespaces = self.ns )            
            eST = self.__parseCV( eSTDom[0])
            crng["endStatus"] = sST

            ePS = r.xpath( "./mif:end/@position", namespaces = self.ns )
            if ePS:
                crng["end"] = ePS[0]
            
            ePSI = r.xpath( "./mif:endInterval", namespaces = self.ns )
            if ePSI:

                ePSIbegin = ePSI[0].xpath( "./@begin", namespaces = self.ns )
                ePSIend = ePSI[0].xpath( "./@end", namespaces = self.ns )

                if ePSIbegin and ePSIend:
                    crng["eint"] = {'begin':ePSIbegin[0], 'end':ePSIend[0]}
            
            lnk =  r.xpath( "./mif:isLink/text()", namespaces = self.ns )
            if lnk:
                crng["link"] = str(lnk[0])

            rng.append( crng )
        return rng
                
    def __parseInteractor( self, dom ):

        idix = {}
        i10r = {}
        i10r['dom']=dom

        i10r['rid'] =  dom.xpath( "./@id", namespaces = self.ns )[0]
    
        SL =  dom.xpath( "./mif:names/mif:shortLabel/text()",
                          namespaces = self.ns )
        if len(SL) > 0:
            i10r[ 'label' ] = SL[0]
        else:
            i10r[ 'label' ] = ''

            
        FN =  dom.xpath( "./mif:names/mif:fullName/text()",
                         namespaces = self.ns )
        if len( FN ) > 0:
            i10r[ 'name' ] = FN[0]
        else:
            i10r[ 'name' ] = ''
            
        i10r[ 'attr' ] =  dom.xpath( "./mif:names/mif:alias/text()",
                                     namespaces = self.ns )

        #xrefs
        xrefDom = dom.xpath( "./mif:xref", namespaces = self.ns )
        if xrefDom:
            (i10r['pxref'], i10r['sxref']) = self.__parseXref( xrefDom[0] )        
            
        itpDom= dom.xpath( "./mif:interactorType", namespaces = self.ns )
        i10r[ 'type' ] =  self.__parseCV( itpDom[0] )

        # note: optional (missing for eg small molecules
        #<organism ncbiTaxId="83333">
        # <names>
        #  <shortLabel>ecoli</shortLabel>
        #  <fullName>Escherichia coli (strain K12)</fullName>
        # </names>
        #</organism>
        
        spcDom= dom.xpath( "./mif:organism", namespaces = self.ns )
        
        if spcDom:
            i10r[ 'species' ] =  self.__parseHost( spcDom[0] )        
            
        #sequence
        seqDom= dom.xpath( "./mif:sequence/text()", namespaces = self.ns )
        if seqDom:
            i10r[ 'sequence' ] =  seqDom[0]
        
        return i10r
        
    def __parseRefList( self, ref ):
        ret = []
        for r in ref:
            #print(ET.tostring(r))
            acID = r.xpath( "./@id", namespaces = self.ns )
            ns = r.xpath( ".//@db", namespaces = self.ns )
            nsID = r.xpath( ".//@dbAc", namespaces = self.ns )
            verID  = r.xpath( ".//@version", namespaces = self.ns )
            refType  = r.xpath( ".//@refType", namespaces = self.ns )
            refTypeAc  = r.xpath( ".//@refTypeAc", namespaces = self.ns )

            ref = {}
            if acID:
                ref['ac'] = acID[0]
            if ns:
                ref['ns'] = ns[0]
            if nsID:
                ref['nsAc'] = nsID[0]
            if verID:
                ref['ver'] = verID[0]
            if refType:
                ref['refType'] = refType[0]
            if refTypeAc:
                ref['refTypeAc'] = refTypeAc[0]

            ret.append( ref )
            
        return ret
    
    def __parseCV( self, cvdom, xref=False ):

        cv = {}
        
        cvID = cvdom.xpath( "./mif:xref/mif:primaryRef/@id",
                            namespaces = self.ns )
        if cvID:
            cv['ac']=cvID[0]
        
        cvDB = cvdom.xpath( "./mif:xref/mif:primaryRef/@db",
                            namespaces = self.ns )
        if cvDB:
            cv['ns']=cvDB[0]
                
        cvDBID = cvdom.xpath( "./mif:xref/mif:primaryRef/@dbAc",
                              namespaces = self.ns )
        if cvDBID:
            cv['nsAc']=cvDBID[0]
                
        cvSL = cvdom.xpath( "./mif:names/mif:shortLabel/text()",
                            namespaces = self.ns )

        if cvSL:
            cv['label']=cvSL[0]
        
        cvFN = cvdom.xpath( "./mif:names/mif:fullName/text()",
                            namespaces = self.ns )

        if cvFN:
            cv['name']=cvFN[0]

        if xref:
            xrefDom = cvdom.xpath( "./mif:xref", namespaces = self.ns )
            (cv['pxref'], cv['sxref']) = self.__parseXref( xrefDom[0] )        
        
        return cv
    

    def __parseAtt( self, adom ):
    
        #<attributeList>
        # <attribute name="author-list" nameAc="MI:0636">McEvoy MM., Hausrath AC., Randolph GB., Remington SJ., Dahlquist FW.</attribute>
        # <attribute name="contact-email" nameAc="MI:0634">fwd@nmr.uoregon.edu</attribute>
        # <attribute name="journal" nameAc="MI:0885">Proceedings of the National Academy of Sciences of the United States of America</attribute>
        # <attribute name="publication year" nameAc="MI:0886">1998</attribute>
        # <attribute name="curation depth" nameAc="MI:0955">imex curation</attribute>
        # <attribute name="full coverage" nameAc="MI:0957">Only protein-protein interactions</attribute>
        # <attribute name="imex curation" nameAc="MI:0959">imex curation</attribute>
        #</attributeList>

        attlist = []
        for a in adom:
            name = a.xpath( "./@name",
                            namespaces = self.ns )
            nameAc = a.xpath( "./@nameAc",
                            namespaces = self.ns )
            value = a.xpath( "./text()",
                             namespaces = self.ns )
            att = {}
            if name:
                att['name'] = name[0]
            if nameAc:
                att['ac'] = nameAc[0]
            if value:
                att['value'] = value[0]

            attlist.append( att )

        return attlist
           
    def __parseHost( self, hdom ):

        host = {'ns':'taxid'}

        host['ac'] = hdom.xpath( ".//@ncbiTaxId",
                                namespaces = self.ns )[0]
        
        host['label'] = hdom.xpath( ".//mif:shortLabel/text()",
                                   namespaces = self.ns )[0]
        
        name = hdom.xpath( ".//mif:fullName/text()",
                          namespaces = self.ns ) 
        if name:
            host['name'] = name[0]
        else:
            host['name'] = host['label']
    
        ctypeDom = hdom.xpath( ".//mif:cellType",
                                 namespaces = self.ns )
        if ctypeDom:
            host['ctype'] = self.__parseCV( ctypeDom[0], xref=True )

            
        return host
    
    def __parseSource( self, entry ):

        source = {}
        
        # source
        #-------

        msrc = entry.xpath( "./mif:source",
                            namespaces = self.ns )[0]        

        source['dom'] = msrc
        
        #  <source releaseDate="2013-09-02+01:00">
        #   <names>
        #    <shortLabel>MINT</shortLabel>
        #    <fullName>MINT, Dpt of Biology, University of Rome Tor Vergata</fullName>
        #   </names>
        #   <xref>
        #    <primaryRef db="psi-mi" dbAc="MI:0488" id="MI:0471" refType="identity" refTypeAc="MI:0356"/>
        #    <secondaryRef db="intact" dbAc="MI:0469" id="EBI-1579228" refType="identity" refTypeAc="MI:0356"/>
        #   </xref>
        #   <attributeList>
        #    <attribute name="url" nameAc="MI:0614">http://mint.bio.uniroma2.it/mint</attribute>
        #    <attribute name="url">http://mint.bio.uniroma2.it/mint</attribute>
        #   </attributeList>
        #  </source>

        label = msrc.xpath( ".//mif:shortLabel/text()",
                            namespaces = self.ns )
        if label:
            source['label'] = label[0]
        else:
            source['label'] = None
            
        name =  msrc.xpath( ".//mif:fullName/text()",
                            namespaces = self.ns )
        if name:
            source['name'] = name[0]
        else:
            source['name'] = source['label']
            
        # bibref
        
        source['bibref'] = self.__parseBibref( msrc )
        
        #xrefs
        xns =  msrc.xpath( "./mif:xref/mif:primaryRef/@db",
                                   namespaces = self.ns )
        if xns:
            source['ns'] =xns[0]

        xac =  msrc.xpath( "./mif:xref/mif:primaryRef/@id",
                           namespaces = self.ns )        
        if xac:
            source['ac'] = xac[0]
                    
        xrefDom = msrc.xpath( "./mif:xref",
                              namespaces = self.ns )
        if xrefDom:
            (source['pxref'], source['sxref']) = self.__parseXref( xrefDom[0] )        

        #attributes
        attlistDom = msrc.xpath( "./mif:attributeList",
                                 namespaces = self.ns )
        if attlistDom:
            source['attList'] = self.__parseAtt( attlistDom[0] )
        
        return source

    def __parseExperiment( self, dom ):

        e10t = {}
        e10t['dom'] = dom
        
        e10t['rid'] =  dom.xpath( "./@id",
                                  namespaces = self.ns )[0]
        self.crid = e10t['rid']
            
        #     <names>
        #         <shortLabel>volkman-2002-1</shortLabel>
        #         <fullName>Structure of the N-WASP EVH1 domain-WIP complex: insight into the molecular basis of Wiskott-Aldrich Syndrome.</fullName>
        #     </names>
        #     <bibref>
        #         <xref>
        #             <primaryRef db="pubmed" dbAc="MI:0446" id="12437929" refType="primary-reference" refTypeAc="MI:0358"/>
        #         </xref>
        #     </bibref>
        
        e10t['label'] = dom.xpath( "./mif:names/mif:shortLabel/text()",
                                   namespaces = self.ns )[0]
        
        name = dom.xpath( "./mif:names/mif:fullName/text()",
                          namespaces = self.ns ) 
        if name:
            e10t['name'] = name[0]
        else:
            e10t['name'] = e10t['label']

        # bibref
        pmidDom = dom.xpath( ".//mif:bibref//mif:primaryRef/@id",
                             namespaces = self.ns )
        if pmidDom:
            e10t['pmid'] = pmidDom[0]

        e10t['bibref'] = self.__parseBibref( dom )        
            
        #     <xref>
        #         <primaryRef db="mint" dbAc="MI:0471" id="MINT-722978" refType="identity" refTypeAc="MI:0356"/>
        #         <secondaryRef db="pubmed" dbAc="MI:0446" id="12437929" refType="secondary-ac" refTypeAc="MI:0360"/>
        #         <secondaryRef db="doi" dbAc="MI:0574" id="10.1016/S0092-8674(02)01076-0" refType="secondary-ac" refTypeAc="MI:0360"/>
        #         <secondaryRef db="intact" dbAc="MI:0469" id="EBI-8558582" refType="identity" refTypeAc="MI:0356"/>
        #         <secondaryRef db="mint" dbAc="MI:0471" id="MINT-5215918" refType="primary-reference" refTypeAc="MI:0358"/>
        #         <secondaryRef db="imex" dbAc="MI:0670" id="IM-26977" refType="imex-primary" refTypeAc="MI:0662"/>
        #     </xref>

        # xref

        imexLst = dom.xpath( ".//mif:xref/mif:*[@refType='imex-primary']/@id",
                             namespaces = self.ns )
        if imexLst is not None and len(imexLst) > 0:
            e10t['imex'] = imexLst[0]
        #else:
        #   print("***>")
        #   print(ET.tostring(dom))
        #   print("<***")    
        xrefDom = dom.xpath( "./mif:xref",
                             namespaces = self.ns )
        if xrefDom:
            (e10t['pxref'], e10t['sxref']) = self.__parseXref( xrefDom[0] )
            
        #<hostOrganismList>
        # <hostOrganism ncbiTaxId="83333">
        #  <names>
        #   <shortLabel>ecoli</shortLabel>
        #   <fullName>Escherichia coli (strain K12)</fullName>
        #  </names>
        # </hostOrganism>
        #</hostOrganismList>

        # exp host
        ehost = dom.xpath( ".//mif:hostOrganism",
                           namespaces = self.ns )
        if ehost:
            e10t['ehost'] = []
            for eh in ehost:
                e10t['ehost'].append( self.__parseHost( eh ))               
                
        #     <interactionDetectionMethod>
        #         <names>
        #             <shortLabel>x-ray diffraction</shortLabel>
        #             <fullName>x-ray crystallography</fullName>
        #             <alias typeAc="MI:0303" type="go synonym">X-ray</alias>
        #             <alias typeAc="MI:1041" type="synonym">X-ray</alias>
        #         </names>
        #         <xref>
        #             <primaryRef db="psi-mi" dbAc="MI:0488" id="MI:0114" refType="identity" refTypeAc="MI:0356"/>
        #             <secondaryRef db="intact" dbAc="MI:0469" id="EBI-1272" refType="identity" refTypeAc="MI:0356"/>
        #             <secondaryRef db="pubmed" dbAc="MI:0446" id="14755292" refType="primary-reference" refTypeAc="MI:0358"/>
        #         </xref>
        #     </interactionDetectionMethod>
            
        intIdMthDom = dom.xpath( ".//mif:interactionDetectionMethod",
                                 namespaces = self.ns )

        #print(ET.tostring(dom))
        e10t['intMth'] = self.__parseCV( intIdMthDom[0] )
        
        #     <participantIdentificationMethod>
        #         <names>
        #             <shortLabel>predetermined</shortLabel>
        #             <fullName>predetermined participant</fullName>
        #             <alias typeAc="MI:1041" type="synonym">predetermined</alias>
        #         </names>
        #         <xref>
        #             <primaryRef db="psi-mi" dbAc="MI:0488" id="MI:0396" refType="identity" refTypeAc="MI:0356"/>
        #             <secondaryRef db="intact" dbAc="MI:0469" id="EBI-1465" refType="identity" refTypeAc="MI:0356"/>
        #             <secondaryRef db="pubmed" dbAc="MI:0446" id="14755292" refType="primary-reference" refTypeAc="MI:0358"/>
        #         </xref>
        #     </participantIdentificationMethod>
        
        pimlst = dom.xpath( ".//mif:participantIdentificationMethod",
                            namespaces = self.ns )

        e10t['prtMth'] = None
        for pim in pimlst:
            e10t['prtMth'] = self.__parseCV( pim )
            break
         
        #<attributeList>
        # <attribute name="author-list" nameAc="MI:0636">McEvoy MM., Hausrath AC., Randolph GB., Remington SJ., Dahlquist FW.</attribute>
        # <attribute name="contact-email" nameAc="MI:0634">fwd@nmr.uoregon.edu</attribute>
        # <attribute name="journal" nameAc="MI:0885">Proceedings of the National Academy of Sciences of the United States of America</attribute>
        # <attribute name="publication year" nameAc="MI:0886">1998</attribute>
        # <attribute name="curation depth" nameAc="MI:0955">imex curation</attribute>
        # <attribute name="full coverage" nameAc="MI:0957">Only protein-protein interactions</attribute>
        # <attribute name="imex curation" nameAc="MI:0959">imex curation</attribute>
        #</attributeList>

        attlistDom = dom.xpath( "./mif:attributeList", namespaces = self.ns )
        if attlistDom:
            e10t['attList'] = self.__parseAtt( attlistDom[0] )            
        
        return e10t

    def __parseBibref( self, dom ):
        
        bibref = None
        brefDom = dom.xpath( "./mif:bibref", namespaces = self.ns )        
        if brefDom:
            # xrefs
            pxref = None
            sxref = None

            xrefDom = brefDom[0].xpath( "./mif:xref", namespaces = self.ns )
            if xrefDom:
                (pxref, sxref) = self.__parseXref( xrefDom[0] )
                
                if pxref is not None or sxref is not None:
                    bibref = {'pxref':pxref, 'sxref':sxref }
                            
            attDom = brefDom[0].xpath( "./mif:attributeList",
                                       namespaces = self.ns )
            if attDom:
                attlst = self.__parseAtt( attDom[0] )            

                if bibref is None:
                    bibref = {'attlst':attlst}
                else:
                    bibref['attlst'] = attlst
        return bibref
    
    def __parseXref(self, dom):

        # xref
        prXRefDom = dom.xpath( "./mif:primaryRef", namespaces = self.ns )
        pxref = self.__parseRefList( prXRefDom )
        
        scXRefDom = dom.xpath( "./mif:secondaryRef", namespaces = self.ns )
        sxref = self.__parseRefList( scXRefDom )

        return ( pxref, sxref)
    
