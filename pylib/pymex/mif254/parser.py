# -*- coding: utf-8 -*-
"""
Created on Mon Jun 29 13:56:57 2020
@author: andrei
"""
#-------------------- IMPORTS -----------------------------------------------------------------------
 
# -*- coding: utf-8 -*-
from lxml import etree
import json

from mif254.utils import *

#-------------------------------- Recursive Parsers --------------------------------------------------

def genericSearch( entry, item ):
    """Recursive search through element tree."""
    
    tag = modifyTag(item)
    #print("TAG:", tag)
    #if item.text and len(item)==0: # We have reached a leaf node: does it have attributes or not?      
    #    if not item.attrib:
    #        return item.text  
    #    else:
    #        return {"text": item.text,"elementAttrib": attribToDict( item.attrib )  }
     
    if tag == "names":
        names = Names( entry )
        return names.parseDom( item )
        #print(tag,'c')

    elif tag == "xref":
        ( id, xref ) = Xref( entry ).parseDom( item )
        return xref
        #print(tag,'d')

    elif tag in ["organism", "hostOrganism" ]:
        ( taxid, org ) = Organism( entry ).parseDom( item )
        return org
        #print(tag,'d')

    elif tag == "feature":
        ( taxid, feature ) = Feature( entry ).parseDom( item )
        return feature    
    
    elif tag=="attribute":    
        return Attribute(entry).parseDom( item ) 
        
    elif tag.endswith( 'List' ):
        tag = tag[:-4]  #strip trailing 'List'
        #print("LISTED", tag)
        #if tag=="attribute":
        #    print("$")
        #    return Attribute(entry).parseDom( item )

        #else:
        return ListedElement( entry ).parseDom( item )
    
    elif isCvTerm(item):
        cvterm = CvTerm(entry)
        return cvterm.parseDom( item )
    
    elif item.text and len(item)==0: # We have reached a leaf node: does it have attributes or not?      
        if not item.attrib:
            return item.text  
        else:
            return {"value": item.text,"elementAttrib": attribToDict( item.attrib )  }

    else:
        data={}
        if item.attrib:
            attribDict =  attribToDict(item.attrib)
            data["elementAttrib"] = attribToDict(item.attrib)
            for a in attribDict:
                data[a] = attribDict[a]
            
        for child in item: 
            tag = modifyTag(child)
            data[tag] = genericSearch( entry, child )

        #print(tag,'f')
    
        return data

#------------------------------ CLASSES ------------------------------------------------------

class Mif254Parser():
    """Parses a mif file associated with a filename. Saves to Mif254Record object."""

    def __init__(self,debug=False):
        self.debug = debug
        
    def parse( self, filename ):
        "foo"
        mif = Mif254Record()
        mif.parseDom( filename )
        return mif

class Mif254Record():
    """Mif record representation."""

    def __init__(self):
        self.root = {"entries":[]}
    
    @property
    def entry(self):
        return self.getEntry()
    
    def getEntry(self, id = 0):
        if len(self.root) > id:
            return Entry(self.root, id)
        else:
            return None
    
    @property          
    def interaction(self):
        
        ret = []
        
        for i in Entry( self.root ).interaction:
            ret.append( self.getEntry().getInteraction(id) )
        
        #return Entry(self.root).interaction
        return ret
        
    def __getitem__(self, id):
        return self.getEntry().getInteraction(id)
    
    def parseDom( self, filename ):
        
        record = etree.parse( filename )
        entrySet = record.xpath("/x:entrySet",namespaces=NAMESPACES)
        self.root["elementAttrib"] = attribToDict(entrySet[0].attrib)
        entries = record.xpath( "/x:entrySet/x:entry", namespaces=NAMESPACES )
        for entry in entries:
            entryElem = Entry( self.root )
            self.root["entries"].append( entryElem.parseDom( entry ) )

    def parseJson(self, file ):
        self.root = json.load( file )
        return self

    def toJson(self):
        return json.dumps(self.root, indent=2)

    def toMif( self, ver="254" ):
                
        rootDom = etree.Element( MIF + "entrySet", nsmap=NAMESPACES_TOMIF)

        # LS: these got to be cratated from scratch as they might be absent
        #     or different than what's needed for mif254 (what if mif300 was read?)   
        #for attribkey,attribval in self.root["elementAttrib"].items():
        #    root.attrib[attribkey] = attribval

        if ver=="254":
            rootDom.attrib["level"] = "2"
            rootDom.attrib["version"] = "5"
            rootDom.attrib["minorVersion"] = "4" 
        
        for entry in self.root["entries"]:            
            #entryElem = etree.Element( "entry", nsmap=nsmap)
            #for key, val in entry.items():               
            #    print("ENTRY:", key,type(val))
            #    #elem = genericMifGenerator(key,val)
            #    if elem is not None:
            #        entryElem.append( elem )
            (entryDom, curid) = Entry(self.root).toMif( entry, curid=1, ver=ver ) 
            rootDom.append( entryDom ) 
                    
        return etree.tostring( rootDom, pretty_print=True )
    
class Entry():
    
    def __init__( self, root , id = 0):
        self.data = { "_index":{} }
        self.root = root
        self.id = id
    
    def __getitem__( self, id ):
        return self.getInteraction( id )

    @property
    def interaction(self):        
        return self.root[self.id]["interaction"] 

    def getInteraction( self, id, eid=None ):
        if eid is not None:
            return Interaction( self.root[eid], id)
        else:       
            return Interaction(self.root[self.id],id)

    def toMif(self, entry, curid=1, ver="254"):

        entryDom = etree.Element( MIF + "entry", nsmap=NAMESPACES_TOMIF)
                         
        if "source" in entry:
            #sourceDom = etree.SubElement( parent, MIF + "source" )
            (sourceDom, curid) = Source( self.root ).toMif( entry["source"],
                                                            curid, ver = ver )
            entryDom.append( sourceDom )

        # for now, interaction list only (this enforces expanded version) 
        # next iteration might offer chioce before expanded and compact
        # version

        if "interaction" in entry and len(entry["interaction"]) > 0:
            listDom = etree.Element( MIF + "interactionList", nsmap=NAMESPACES_TOMIF )
            entryDom.append( listDom )
            for intn in entry["interaction"]:
                (intnDom, curid) = Interaction( self.root ).toMif( intn, curid, ver=ver )
                listDom.append( intnDom )
                
        return ( entryDom, curid )
                
    def parseDom( self, dom ):
        for item in dom:
            tag = item.tag[LEN_NAMESPACE:]            
            if tag == 'source':
                self.data["source"] = Source( self.data ).parseDom( item )
                
            elif tag == 'experimentList':                
                self.data.setdefault( tag[:-4], [] )
                self.data['_index'].setdefault( tag[:-4], {} )
                
                expElem = item.xpath( "x:experimentDescription", namespaces=NAMESPACES )            
                for exp in expElem:                    
                    (cId, cExp) =  Experiment( self.data ).parseDom( exp )                    
                    self.data["experiment"].append (cExp )
                    self.data['_index'][tag[:-4]][str(cId)] = cExp
                    
            elif tag == 'interactorList':
                self.data.setdefault(tag[:-4], [] )
                self.data['_index'].setdefault( tag[:-4], {} )
                
                intrElem = item.xpath( "x:interactor", namespaces=NAMESPACES )
                for intr in intrElem:
                    (cId, cInt) =  Interactor( self.data ).parseDom( intr )
                    self.data["interactor"].append( cInt ) 
                    self.data['_index'][tag[:-4]][str(cId)] = cExp
                    
            elif tag == 'interactionList':
               self.data.setdefault(tag[:-4], [] )
               self.data['_index'].setdefault( tag[:-4], {} )
                            
               intnElem = item.xpath( "x:interaction", namespaces=NAMESPACES )
               for intn in intnElem:
                   (cId, cIntn) =  Interaction( self.data ).parseDom( intn )
                   self.data["interaction"].append( cIntn )
                   self.data['_index'][tag[:-4]][str(cId)] = cExp
                   
            elif tag == 'availabilityList':
                self.data.setdefault(tag[:-4], [] )
                self.data['_index'].setdefault( tag[:-4], {} )
                               
                avlbElem = item.xpath( "x:availability", namespaces=NAMESPACES )
                for avlb in avlbElem:
                    (cId, cAvlb) =  Availability( self.data ).parseDom(  avlb  )
                    self.data["availability"].append( cAvlb )
                    self.data['_index'][tag[:-4]][str(cId)] = cExp
        
        return self.data

class Source():
    
    def __init__( self, entry ):
        self.data={}
        self.entry = entry

    def parseDom( self, dom ):
        if(isinstance( dom, str)):
            record = etree.parse( dom )
            dom = record.xpath( "/x:entrySet/x:entry/x:source",
                                namespaces=NAMESPACES )[0]        

        reldate = dom.xpath( "./@releaseDate", namespaces=NAMESPACES )
        for rd in reldate:
            self.data['releaseDate'] = str(rd)
            
        for item in dom:
            tag = modifyTag(item)
            
            if tag =="attributeList":
                self.data.setdefault( tag[:-4], [] ) 
                self.data[tag[:-4]] = Attribute(self.entry).parseDom( item )
            else:
                self.data[tag] = genericSearch( self.entry, item )
            
        #self.data["elementAttrib"]=attribToDict(dom.attrib) #sources have attributes
        
        return self.data
    
    def toMif( self, source, curid, ver = "mif254" ):
        sourceDom = etree.Element( MIF + "source", nsmap=NAMESPACES_TOMIF)
               
        # build source content here

        if "releaseDate" in source:
            sourceDom.attrib["releaseDate"] = str( source["releaseDate"] )
        else:
            #set to current date ("2020-03-13Z" format)
            pass    #FIX ME

        if "names" in source:
            (namesDom, curid) = Names( self.entry ).toMif( source["names"],
                                                           curid, ver=ver ) 
            sourceDom.append( namesDom ) 
            
        if "xref" in source:
            (xrefDom, curid) = Xref( self.entry ).toMif( source["xref"],
                                                         curid, ver=ver ) 
            sourceDom.append( xrefDom ) 
                    
        if "attribute" in source:
            (attrDom, curid) = Attribute( self.entry ).toMif( source["attribute"],
                                                              curid, ver=ver )
            sourceDom.append( attrDom )
        
        return (sourceDom, curid)
    
class Experiment():
    def __init__( self, entry ):
        self.data = {}
        self.entry = entry
        
    def parseDom( self, dom ):

        if(isinstance(dom, str)):
            record = etree.parse( dom )
            dom = record.xpath( "/x:entrySet/x:entry/x:experimentList/x:experiment",
                                namespaces=NAMESPACES)[0]
        
        id = dom.xpath("./@id", namespaces=NAMESPACES )
        self.data['_id'] = str( id[0] )
        for item in dom:
            tag = item.tag[LEN_NAMESPACE:]
            if tag =="attributeList":
                self.data.setdefault( tag[:-4], [] ) 
                self.data[tag[:-4]] = Attribute(self.entry).parseDom( item )
            
            elif tag =="hostOrganismList":
                self.data.setdefault( tag[:-4], [] ) 
                self.data[tag[:-4]] = ListedElement( self.entry ).parseDom( item )  
            
            else:                
                tag = modifyTag(item)
                self.data[tag] = genericSearch( self.entry, item )

        #element with id attribute: return (id,data) tuple   
        return ( str(id[0]), self.data )

    
    def toMif( self, explst, curid, ver = "mif254",compact=False ):
        exptlstDom = etree.Element( MIF + "experimentList", nsmap=NAMESPACES_TOMIF)
               
        # build experiemnt list here

        for expt in explst:
            exptDom = etree.Element( MIF + "experimentDescription", nsmap=NAMESPACES_TOMIF)
            curid += 1
            exptDom.attrib["id"]= str(curid)
            
            if "names" in expt:
                (namesDom, curid) = Names( self.entry ).toMif( expt["names"],
                                                               curid, ver=ver ) 
                exptDom.append( namesDom ) 

            if "bibref" in expt:
                bibrefDom = etree.Element( MIF + "bibref", nsmap=NAMESPACES_TOMIF)

                if 'xref' in expt['bibref']:
                    (bxrefDom, curid) = Xref( self.entry ).toMif( expt["bibref"]["xref"],
                                                                  curid, ver=ver ) 
                    bibrefDom.append( bxrefDom ) 
                
                if 'attribute' in expt['bibref']:
                    (attrDom, curid) = Attribute( self.entry ).toMif( expt['bibref']['attribute']) 
                    bibrefDom.append( attrDom ) 
                    
                exptDom.append( bibrefDom )
                
            if "xref" in expt:
                (xrefDom, curid) = Xref( self.entry ).toMif( expt["xref"],
                                                             curid, ver=ver ) 
                exptDom.append( xrefDom ) 

            if "hostOrganism" in expt and len(expt["hostOrganism"]) >0 :
                holstDom = etree.Element( MIF + "hostOrganismList", nsmap=NAMESPACES_TOMIF)
                for ho in expt["hostOrganism"]:
                    print(ho)
                    (hoDom, curid) = Organism( self.entry ).toMif( "hostOrganism", ho,
                                                                   curid, ver=ver ) 
                    holstDom.append( hoDom ) 
                exptDom.append( holstDom ) 

            for cvt in ["interactionDetectionMethod",
                        "participantIdentificationMethod",
                        "featureDetectionMethod"]:
                if cvt in expt:
                    (cvtDom, curid) = CvTerm( self.entry ).toMif( cvt,
                                                              expt[cvt],
                                                              curid, ver=ver ) 
                    exptDom.append( cvtDom ) 
                
            
            if "confidence" in expt:
                pass  #FIX ME
                        
            if "attributes" in expt:
                (attrDom, curid) = Attribute( self.entry ).toMif( expt["attribute"],
                                                                  curid, ver=ver ) 
                exptDom.append( attrDom ) 

            
            exptlstDom.append( exptDom )
    
        return (exptlstDom, curid)
    
class Interactor():
    def __init__( self, entry ):
        self.data={}
        self.entry = entry

    def parseDom( self, dom ):

        if(isinstance(dom, str)):
            record = etree.parse(dom)
            dom = record.xpath( "/x:entrySet/x:entry/x:interactorList",
                                namespaces=NAMESPACES)[0]
            
        id = dom.xpath("./@id", namespaces=NAMESPACES )
        self.data["_id"] = str(id[0])
        for item in dom:
            tag = modifyTag(item)

            if tag =="attributeList":
                self.data.setdefault( tag[:-4], [] ) 
                self.data[tag[:-4]] = Attribute(self.entry).parseDom( item )

            else:   
                self.data[tag] = genericSearch( self.entry, item )

        #element with id attribute: return (id,data) tuple   
        return ( str(id[0]), self.data )

    def toMif( self, interactor, curid=1, ver="mif254", compact=False):

        intrDom = etree.Element( MIF + "interactor", nsmap=NAMESPACES_TOMIF)
        curid += 1
        intrDom.attrib["id"] = str(curid)

        # build interactor content here
        if 'names' in interactor:
            (namesDom, curid) = Names( self.entry ).toMif( interactor["names"],
                                                           curid, ver=ver ) 
            intrDom.append( namesDom ) 

        if 'xref' in interactor:
            (xrefDom, curid) = Xref( self.entry ).toMif( interactor["xref"],
                                                         curid, ver=ver ) 
            intrDom.append( xrefDom ) 

        if 'interactorType' in interactor:
            (itpDom, curid) = CvType( self.entry ).toMif( 'interactorType',
                                                          interactorType['interactorType'],
                                                          curid, ver=ver )
            intrDom.append( itpDom ) 

        
        if 'organism' in interactor:
            (orgDom, curid) = Organism( self.entry ).toMif( "hostOrganism",
                                                            interactor['organism'],
                                                            curid, ver=ver ) 
            intrDom.append( orgDom ) 
        
        if 'sequence' in interactor:
            seqDom = etree.Element( MIF + "sequence", nsmap=NAMESPACES_TOMIF)
            seqDom.text=str(interactor['sequence'])
            intrDom.append( seqDom )
            
        if 'attribute' in interactor:
            (attrDom, curid) = Attribute( self.entry ).toMif( interactor["attribute"],
                                                              curid, ver=ver )
            intrDom.append( attrDom )
                    
        return (intrDom, curid) 

    
class Interaction():
    def __init__( self, entry, id=0 ):
        self.data={}
        self.entry = entry
        self.id=id
        
    @property
    def participant(self):
        return self.entry["interaction"][self.id]["participant"]

    @property
    def itype(self):
        return self.entry["interaction"][self.id]["interactionType"]

    @property
    def source(self):
        return self.entry["source"]


    def toMif( self, intn, curid=1, ver="mif254", compact=False):

        intnDom = etree.Element( MIF + "interaction", nsmap=NAMESPACES_TOMIF)
        curid += 1
        intnDom.attrib["id"] = str(curid)

        # build interaction content here
        if 'names' in intn:
            (namesDom, curid) = Names( self.entry ).toMif( intn["names"],
                                                           curid, ver=ver ) 
            #intnDom.append( namesDom ) 
            
        if  'xref' in intn:
            (xrefDom, curid) = Xref( self.entry ).toMif( intn["xref"],
                                                         curid, ver=ver ) 
            #intnDom.append( xrefDom ) 
            
        if 'experiment' in intn and len(intn['experiment']) > 0:
            (exptDom, curid) = Experiment( self.entry ).toMif( intn["experiment"],
                                                               curid, ver=ver,
                                                               compact=compact ) 
            #intnDom.append( exptDom )
            
        if 'participant' in intn and len(intn["participant"]) > 0:
            plstDom = etree.Element( MIF + "participantList", nsmap=NAMESPACES_TOMIF)

            for prpt in intn["participant"]:            
                (prptDom, curid) = Participant( self.entry ).toMif( prpt,
                                                                    curid, ver=ver,
                                                                    compact=compact )
                plstDom.append(prptDom)
            intnDom.append( plstDom )

            
        if 'interactionType' in intn:
            (itpDom, curid) = CvTerm( self.entry ).toMif( 'interactionType',
                                                          intn['interactionType'],
                                                          curid, ver=ver )
            intnDom.append( itpDom ) 

        
        if 'modelled'in intn:
            pass #FIX ME
        
        if 'intraMolecular'in intn:
            pass #FIX ME

        if 'negative' in intn:
            pass #FIX ME

        if 'attribute' in intn:
            (attrDom, curid) = Attribute( self.entry ).toMif( intn["attribute"],
                                                              curid, ver=ver )
            intnDom.append( attrDom )
        
        return (intnDom, curid)
    
    def parseDom( self, dom ):
        
        if(isinstance(dom, str)):
            record = etree.parse(dom)
            dom = record.xpath( "/x:entrySet/x:entry/x:interactionList",
                                namespaces=NAMESPACES)[0]       
        
        idata = {}
        id = dom.xpath("./@id", namespaces=NAMESPACES )
        idata["_id"] = str(id[0])
        for item in dom:
            tag = item.tag[LEN_NAMESPACE:]

            if tag == "experimentList":

                idata[tag[:-4]] = []

                # expanded form: <experimentDescription>...</experimentDescription>
                
                expElem = item.xpath( "x:experimentDescription", namespaces=NAMESPACES )
                for exp in expElem:
                    
                    (cId, cExp) =  Experiment( self.entry ).parseDom( exp )
                    idata[tag].append( cExp )
                    self.root
                #  compact form: <experimentRef>...</experimentRef>
                    
                refElem = item.xpath( "x:experimentRef/text()", namespaces=NAMESPACES )
                #print(self.entry["_index"]["experiment"].keys())
                for ref in refElem:
                    idata[tag[:-4]].append( self.entry["_index"]["experiment"][ref] ) 

            elif tag == "participantList":
                idata[tag[:-4]] = []
                prtElem = item.xpath( "x:participant", namespaces=NAMESPACES )
                for prt in prtElem: 
                    (cId, cPrt) =  Participant( self.entry ).parseDom( prt )
                    idata[tag[:-4]].append( cPrt )
                
            elif tag in ["modelled","intraMolecular","negative"]:
                idata[tag] = "bool"
                
            elif tag =="confidenceList":
                idata[tag[:-4]] = "conf"  #skip fo rnow
                
            elif tag =="parameterList":
                idata[tag[:-4]] = "param"  #skip for now

            elif tag =="attributeList":
                idata.setdefault( tag[:-4], [] )
                idata[tag[:-4]] = Attribute(self.entry).parseDom( item )
            else:
                tag = modifyTag(item)
                idata[tag] = genericSearch(self.entry, item)
                
        # idata should look like
        #{
        # "xref": {whatever Xref.parseDom() returns}
        # "names":{whatever Names.parseDom() returns}
        # "availability": {whatever Availability.parseDom() returns
        #                  or the value corresponding to availabilityRef
        #                  taken from entry["availability"] 
        #                 },
        # "experiment": [{..},{..},{..}], the values correspond to the data        
        #                                 field returned by 
        #                                 Experiment().parseDom() or to 
        #                                 entry["experiment"] value 
        #                                 corresponding to experimentRef
        # "participant":[{..},{..},{..}], the values correspond to the data
        # ...                             field returned by 
        #}                                Participant().parseDom() 
                
        #element with id attribute: return (id,data) tuple                    
        return ( id[0], idata )

    
class Participant():
    def __init__(self, entry):
        self.data = {}
        self.entry = entry
        
    def parseDom( self, dom ):
        # build participant here 
        pdata = {}
        id = dom.xpath("./@id", namespaces=NAMESPACES )
        pdata["_id"] = str(id[0])
        for item in dom:
            tag = item.tag[LEN_NAMESPACE:]
            
            if tag == "interactorRef":        
                refElem = item.xpath("text()")
                for ref in refElem:
                    pdata["interactor"] = self.entry["_index"]["interactor"][str(ref)]

            elif tag == "interactor":
                (cId, cInt) =  Interactor( self.data ).parseDom( item )
                self.entry['_index'][tag][str(cId)] = cInt
                pdata["interactor"].append( cInt )                
                
            elif tag.endswith('List'):
                pdata.setdefault( tag[:-4], [] )
                pdata[tag[:-4]] = ListedElement( self.data ).parseDom( item )

            else:
                tag = modifyTag(item)
                pdata[tag] = genericSearch(self.entry,item)
                
        # data should look like
        #{
        # "names":{whatever Names.parseDom() returns}
        # "xref": {whatever Xref.parseDom() returns}
        # "interactor":{..}, the value corresponds        
        #                    to the data field returned by 
        #                    Interactor().parseDom() or to 
        #                    entry["interactor"] value 
        #                    corresponding
        #  "interactionRef":{ interactionRef text },
        #  "participantIdentMethod": [{..}],
        #  "biologicalRole": {},
        #  "experimentalRole":[{..}],    cvTerm (ignore expRefList for now)
        #  "experimentalPreparation":[{..}], cvTerm (ignore expRefList for now)
        #  "experimentalInteractor":[{..}], interactor (ignore expRefList for now)
        #  "feature" : [{..}],     ignore for now
        #  "hostOrganism": [{..}], ignore for now 
        #  "confidence": [{..}],   ignore for now 
        #  "parameter": [{..}],    ignore for now
        #  "attribute": [{..},{..}], the values correspond
        #                            to the values returned
        #                            by Attribute().parseDom()
        #element with id attribute: return (id,data) tuple    
        return ( str(id[0]), pdata )

    def toMif( self, participant, curid=1, ver="mif254", compact=False):

        prptDom = etree.Element( MIF + "participant", nsmap=NAMESPACES_TOMIF)
        curid += 1
        prptDom.attrib["id"] = str(curid)

        print("PPT:", participant.keys())        
        # build participant content here
        if 'names' in participant:
            (namesDom, curid) = Names( self.entry ).toMif( participant["names"],
                                                           curid, ver=ver ) 
            prptDom.append( namesDom ) 
            
        if 'xref' in participant:
            (xrefDom, curid) = Xref( self.entry ).toMif( participant["xref"],
                                                         curid, ver=ver ) 
            prptDom.append( xrefDom ) 
            
        if 'interactor' in participant:
            (intrDom, curid) = Interactor( self.entry ).toMif( participant["interactor"],
                                                               curid, ver=ver ) 
            prptDom.append( intrDom )

        if 'participantIdentificationMethod' in participant:
            pass #FIX ME
        
        if 'biologicalRole'in participant:
            pass #FIX ME
        
        if 'experimentalRole'  in participant:
            pass #FIX ME
        
        if 'experimentalPreparation' in participant:
            pass #FIX ME
        
        if 'feature' in participant and len(participant['feature'])> 0:
            flstDom = etree.Element( MIF + "featureList", nsmap=NAMESPACES_TOMIF)
            for ftr in participant["feature"]:
                (ftrDom, curid) = Feature( self.entry ).toMif( ftr,
                                                               curid, ver=ver ) 
                flstDom.append( ftrDom ) 
            prptDom.append( flstDom ) 
                    
                    
        if 'hostOrganism' in participant:
            if "hostOrganism" in participant and len(participant["hostOrganism"]) >0 :
                holstDom = etree.Element( MIF + "hostOrganismList", nsmap=NAMESPACES_TOMIF)
                for ho in participant["hostOrganism"]:
                    
                    (hoDom, curid) = Organism( self.entry ).toMif( "hostOrganism", ho,
                                                                   curid, ver=ver ) 
                    holstDom.append( hoDom ) 
                prptDom.append( holstDom ) 

        
        if 'confidence' in participant:
            pass #FIX ME
        
        if 'parameter' in participant:
            pass #FIX ME
        
        if 'attribute' in participant:
            (attrDom, curid) = Attribute( self.entry ).toMif( participant["attribute"],
                                                              curid, ver=ver )
            prptDom.append( attrDom )

        return (prptDom, curid)
        
    
class Names():
    def __init__(self, entry ):
        self.entry = entry
        
    def parseDom( self, dom ):        
        ndata = {}
        for item in dom:
            tag = item.tag[LEN_NAMESPACE:]
            if tag == "shortLabel" or tag == "fullName":
                ndata[tag] = item.text
            else:
                if not "alias" in ndata.keys():
                    ndata["alias"] = []
                modifiedAttrib = attribToDict(item.attrib)
                modifiedAttrib["value"] = item.text
                ndata["alias"].append(modifiedAttrib)
        # should return, eg 
        #{
        #  "shortLabel": "DIP",
        #  "fullName": "Database of Interacting Proteins",
        #  "alias: ["alias1","alias2","alias3"]
        #}        
        return ndata   

    def toMif( self, names, curid=1, ver="mif254"):

        namesDom = etree.Element( MIF + "names", nsmap=NAMESPACES_TOMIF)
    
        # build names content here
        
        if 'shortLabel' in names:
            shortDom = etree.Element( MIF + "shortLabel", nsmap=NAMESPACES_TOMIF)
            shortDom.text = names['shortLabel']
            namesDom.append( shortDom )
        else:
            shortDom = etree.Element( MIF + "shortLabel", nsmap=NAMESPACES_TOMIF)
            shortDom.text = 'N/A'
            namesDom.append( shortDom )

        if 'fullName' in names:
            fullDom = etree.Element( MIF + "fullName", nsmap=NAMESPACES_TOMIF)
            fullDom.text = names['fullName']
            namesDom.append( fullDom )
        else:
            pass #FIX ME

        return (namesDom, curid)
    
class Xref():
    def __init__( self, entry ):
        #self.data={}
        self.entry = entry
        
    def parseDom( self, dom ):
        #dom = dom.xpath(".",namespaces=NAMESPACES)[0]
        #self.data = genericSearch( self.entry, dom)
        xdata = { '_index': {} }
        id = ""
        for item in dom:
            tag = item.tag[LEN_NAMESPACE:]
            if tag == "primaryRef":
                id = item.attrib.get("db")+":"+item.attrib.get("id")
                attribDict = attribToDict(item.attrib)
                xdata["primaryRef"] = attribDict
                xdata["_index"][id] = attribDict

            elif tag == "secondaryRef":
                xdata.setdefault( 'secondaryRef', [] )
                
                db_id = item.attrib.get("db")+":"+item.attrib.get("id")
                attribDict = attribToDict( item.attrib )                                
                xdata["secondaryRef"].append(attribDict)
                xdata["_index"][db_id] = attribDict
                
        return (id, xdata)        

    def toMif( self, xref, curid=1, ver="mif254"):

        xrefDom = etree.Element( MIF + "xref", nsmap=NAMESPACES_TOMIF)
    
        # build xref content here
        
        if 'primaryRef' in xref:
            primaryDom = etree.Element( MIF + 'primaryRef', nsmap=NAMESPACES_TOMIF)
            for attr in xref['primaryRef']:
                print(attr)
                if attr == "attribute":
                    pass  #FIX ME
                else:                    
                    primaryDom.attrib[attr]=xref['primaryRef'][attr]
            xrefDom.append(primaryDom)

        if 'secondaryRef' in xref and len(xref['secondaryRef'])>0:
            for sec in xref['secondaryRef']:
                secDom = etree.Element( MIF + 'secondaryRef', nsmap=NAMESPACES_TOMIF)
                for attr in sec:                    
                    if attr == "attribute":
                        pass  #FIX ME
                    else:
                        secDom.attrib[attr]=sec[attr]
                xrefDom.append(secDom)

        return (xrefDom, curid)
    
class Attribute():
    def __init__( self, entry ):
        #self.data = []
        self.entry = entry
        
    def parseDom( self, dom ):
        attribdata = []
        attrDom = dom.xpath("x:attribute",namespaces=NAMESPACES)
        for attr in attrDom: 
            modifiedAttrib = attribToDict(attr.attrib)
            modifiedAttrib["value"] = attr.text
            attribdata.append(modifiedAttrib)    

        # should return 
        #{"value":"dip@mbi.ucla.edu",    
        # "name":"contact-email"
        # "nameAc":"MI:0634"
        #}
        #print(attribdata)
        return attribdata

    def toMif( self, attrLst, curid=1, ver="mif254"):

        attrLstDom = etree.Element( MIF + "attributeList", nsmap=NAMESPACES_TOMIF)
    
        # build attributes here

        for attr in attrLst:
            attrDom = etree.Element( MIF + 'attribute', nsmap=NAMESPACES_TOMIF)
            for a in attr:
                if a == 'value':
                    attrDom.text = attr[a]
                else:
                    attrDom.attrib[a]=attr[a]
                    
            attrLstDom.append(attrDom)
        
        return (attrLstDom, curid)

    
class Availability():
    def __init__( self, entry ):
        self.entry = entry
        
    def parseDom( self, dom ):
        
        id = dom.attrib.get("id")
        availdata = {"value":dom.text}
        
        #element with id attribute: return (id,data) tuple
        # where data is:
        #{
        #  "value":"availability text here"
        #}
        
        return (id, availdata)


    
class CvTerm():
    def __init__(self, entry):
        self.entry = entry
        
    def parseDom( self, dom ):
        cvdata = {}
        for item in dom:
            tag = item.tag[LEN_NAMESPACE:]
            if tag == "names":                          
                cvdata["names"] = Names(self.entry).parseDom( item )    

            elif tag == "xref":
                (id, term) = Xref(self.entry).parseDom( item )
                cvdata["xref"] = term
                      
        return cvdata

    def toMif( self, ename, cvterm, curid, ver = "mif254" ):
        cvtDom = etree.Element( MIF + ename, nsmap=NAMESPACES_TOMIF)
               
        # build cvterm here
        
        if "names" in cvterm:
            (namesDom, curid) = Names( self.entry ).toMif( cvterm["names"],
                                                           curid, ver=ver ) 
            cvtDom.append( namesDom ) 

        if "xref" in cvterm:
            (xrefDom, curid) = Xref( self.entry ).toMif( cvterm["xref"],
                                                         curid, ver=ver ) 
            cvtDom.append( xrefDom ) 

        if "attribute" in cvterm:
            (attrDom, curid) = Attribute( self.entry ).toMif( cvterm["attribute"],
                                                              curid, ver=ver ) 
            cvtDom.append( attrDom ) 

        return ( cvtDom, curid )

    
class Organism():

    def __init__(self, entry):
        self.entry = entry
        
    def parseDom( self, dom ):
        orgdata = {}

        taxid = dom.xpath("./@ncbiTaxId",namespaces=NAMESPACES)
        
        for t in taxid:
            orgdata['ncbiTaxId'] = str(t)

        for item in dom:
            tag = item.tag[LEN_NAMESPACE:]
            if tag == "names":                          
                orgdata["names"] = Names(self.entry).parseDom( item )            
            else:
                orgdata[tag] = CvTerm(self.entry).parseDom( item )
                    
        return ( str(taxid), orgdata )

    def toMif( self, oname, organism, curid, ver = "mif254" ):
        orgDom = etree.Element( MIF + oname, nsmap=NAMESPACES_TOMIF)
        print(organism.keys())
        # build organism here

        if "ncbiTaxId" in organism: 
            orgDom.attrib["ncbiTaxId"]= organism['ncbiTaxId']
        
        if "names" in organism:
            (namesDom, curid) = Names( self.entry ).toMif( organism["names"],
                                                           curid, ver=ver ) 
            orgDom.append( namesDom ) 

        for cvt in [ "cellType", "compartment", "tissue" ]:
                        
            if cvt in organism:
                (cvtDom, curid) = CvTerm( self.entry ).toMif( cvt, organism[cvt],
                                                              curid, ver=ver )
                orgDom.append( cvtDom ) 

        return ( orgDom, curid )


class Feature():
    def __init__(self, entry):
        self.entry = entry
        
    def parseDom( self, dom ):
        ftrdata = {}

        id = dom.xpath("./@id", namespaces=NAMESPACES )
        ftrdata["_id"] = str(id[0])
        
        for item in dom:
            tag = item.tag[LEN_NAMESPACE:]
            if tag.endswith('List'):                       
                ftrdata[tag[:-4]] = ListedElement( self.entry ).parseDom( item )            
            else:
                ftrdata[tag] = genericSearch( self.entry, item)
                    
        return ( str(id[0]) , ftrdata )

    def toMif( self, feature, curid, ver = "mif254" ):
        featureDom = etree.Element( MIF + 'feature', nsmap=NAMESPACES_TOMIF)

        curid += 1
        featureDom.attrib["id"] = str(curid)
        
        # build feature here
        #FIX ME
        return( featureDom, curid)

    
class ListedElement():
    def __init__(self,entry):
        self.entry = entry
    
    def parseDom( self, dom ):
        eldata = []
        for item in dom:
            eldata.append( genericSearch(self.entry,item) )
        
        return eldata
