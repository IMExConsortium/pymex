import re
import json
import dxf as DXF
from io import StringIO
from lxml import etree as ET

class DXF15Parser():
    """Dxf15 parser.
    """
    def __init__( self ):
                            
        self.ns = { 'dxf': 'http://dip.doe-mbi.ucla.edu/services/dxf15' }
        self._dom = None
        self._dxf = []

    @property
    def dom(self):
        return self._dom

    @property
    def dxf(self):
        return self._dxf
        
    def parse( self, source ):
        """Returns dom/dxf representation of the first <dataset> element
        of a dxf15 file.
        """        
        parser = ET.XMLParser( remove_blank_text=True )
        
        if isinstance( source, str):            
            #source = source.replace("<?xml version='1.0' encoding='UTF-8'?>","")
            source = re.sub(r'<\?xml[^>]+?>', '', source)
            dom = ET.parse(StringIO(source), parser)            
        else:                
            dom = ET.parse( source, parser )
            
        dtslist = dom.xpath( '//dxf:dataset', namespaces = self.ns )
        
        if len(dtslist) == 1:
            self._dom = dtslist[0]
        else:
            self._dom = None

        if self._dom is None:
            return None

        nlst = self._dom.xpath( './dxf:node', namespaces = self.ns )
        
        for n in nlst:
            nn = self.__parseNode( n )
            if nn is not None:
                self._dxf.append( nn )

        #return self._dxf
        return DXF.DXF15Record( self._dxf, self._dom )
    

    def __parseNode( self, ndom ):

        #<dxf:node ac="DIP-2612E" ns="dip" id="1">
        #  <dxf:type name="link" ac="dxf:0004" ns="dxf"/>
        #  <dxf:label>DIP-2612E</ns2:label>
        #  <dxf:xrefList>...</dxf:xrefList>
        #  <dxf:attrList>...</dxf:attrList>
        #  <dxf:partList>...</dxf:partList>
        #</dxf:node>

        node = {}
        #      { 'ns' : None, 'ac' : None, 'type' : None, 
        #         'label' : None, 'name' : None,
        #         'xref' : None, 'attr': None, 'part': None }
        
        # ns/ac (id ignored)

        nsl = ndom.xpath( './@ns', namespaces = self.ns)
        acl = ndom.xpath( './@ac', namespaces = self.ns)

        if nsl:
            node['ns'] = nsl[0]

        if acl:
            node['ac'] = acl[0]
        
        # type
        tpl = ndom.xpath( './dxf:type', namespaces = self.ns)
        if tpl:
            node['type'] = self.__parseType( tpl[0] ) 
            
        # label
        labell = ndom.xpath( './dxf:label/text()', namespaces = self.ns)        
        if labell:
            node['label'] = labell[0]
        
        # name
        namel = ndom.xpath( './dxf:name/text()', namespaces = self.ns)        
        if namel:
            node['name'] = namel[0]

        #xrefs
        xrefl = ndom.xpath( './dxf:xrefList/dxf:xref', namespaces = self.ns)        
        if xrefl:
            node['xref'] = []
            for x in xrefl:
                node['xref'].append( self.__parseXref( x ) )
                
        # attrs
        attrl = ndom.xpath( './dxf:attrList/dxf:attr', namespaces = self.ns)
        if attrl:
            node['attr'] = []
            for a in attrl:
                node['attr'].append( self.__parseAttr( a ) )
                                             
        # parts
        partl = ndom.xpath( './dxf:partList/dxf:part', namespaces = self.ns)        
        if partl:
            node['part'] = []
            for p in partl:
                node['part'].append( self.__parsePart( p ) )
        
        # others (ignored)
        
        return node

    def __parseType( self, tdom ):

        #<dxf:type name="evidence" ac="dxf:0015" ns="dxf">
        #  <dxf:node> ... </dxf:node>
        #</dxf:type>
                
        type = {}
        #      { 'ns': None, 'ac': None, 'name': None,
        #        'node': None }
        
        tnml = tdom.xpath( './@name', namespaces = self.ns )
        if tnml:
            type['name'] = tnml[0]
            
        tnsl = tdom.xpath( './@ns', namespaces = self.ns )
        if tnsl:
            type['ns'] = tnsl[0]
            
        tacl = tdom.xpath( './@ac', namespaces = self.ns )
        if tacl:
            type['ac'] = tacl[0]
            
        tndl = tdom.xpath( './dxf:node', namespaces = self.ns )
        if tndl:
            type['node'] = self.__parseNode( tndl[0] )

        return type

    
    def __parseXref( self, xdom ):

        #<dxf:xref type="published-by" typeAc="dxf:0040"
        #          typeNs="dxf" ac="MI:0465" ns="dip">
        #    <dxf:node>...</dxf:node>
        #</dxf:xref>
                
        xref = {}
        #      { 'ns' : None, 'ac': None, 'node': None,
        #        'type': None, 'typeNs': None, 'typeAc': None }

        # ns 
        nsl = xdom.xpath( './@ns', namespaces = self.ns)
        if nsl:
            xref['ns'] = nsl[0]

        # ac 
        acl = xdom.xpath( './@ac', namespaces = self.ns)
        if acl:
            xref['ac'] = acl[0]

        # type
        nml = xdom.xpath( './@type', namespaces = self.ns)
        if nml:
            xref['type'] = nml[0]

        # typeNs
        tnl = xdom.xpath( './@typeNs', namespaces = self.ns)
        if acl:
            xref['typeNs'] = tnl[0]

        # typeAc 
        tal = xdom.xpath( './@typeAc', namespaces = self.ns)
        if acl:
            xref['typeAc'] = tal[0]

        # node
        tnl = xdom.xpath( './dxf:node', namespaces = self.ns)
        if tnl:
            xref['node'] = self.__parseNode( tnl[0] )
            
        return xref
            
    def __parseAttr( self, adom ):

        #<dxf:attr name="part-list-status" ac="dip:0006" ns="dip">
        #   <dxf:value ac="dip:0302" ns="dip">complete</ns2:value>
        #   <dxf:node>...</dxf:node>
        # </dxf:attr>
                                  
        attr = {}
        #      { 'ns' : None, 'ac': None, 'name': None,
        #        'value': None, 'node':None }

        # ns 
        nsl = adom.xpath( './@ns', namespaces = self.ns)
        if nsl:
            attr['ns'] = nsl[0]

        # ac 
        acl = adom.xpath( './@ac', namespaces = self.ns)
        if acl:
            attr['ac'] = acl[0]

        # name 
        nml = adom.xpath( './@name', namespaces = self.ns)
        if nml:
            attr['name'] = nml[0]

        # value 
        val = adom.xpath( './dxf:value', namespaces = self.ns)
        if val:
            attr['value'] = {} # {'ns': None,'ac': None,'value': None }
            cval = val[0]

            # value ns 
            vnsl = cval.xpath( './@ns', namespaces = self.ns)
            if vnsl:
                attr['value']['ns'] = vnsl[0]
            
            # value ac 
            vacl = cval.xpath( './@ac', namespaces = self.ns) 
            if vacl:
                attr['value']['ac'] = vacl[0]

            # value text 
            vtxl = cval.xpath( './text()', namespaces = self.ns) 
            if vtxl:
                attr['value']['value'] = vtxl[0]
            
        # node
        ndl = adom.xpath( './dxf:node', namespaces = self.ns)
        if ndl:
             attr['node'] = self.__parseNode( ndl[0] )

        return attr

            
    def __parsePart( self, pdom ):

        #<dxf:part id="3" name="CEG1{A}">
        #  <dxf:type name="linked-node" ac="dxf:0010" ns="dxf"/>
        #  <dxf:node>...</dxf:node>
        #  <dxf:xrefList>...</dxf:xrefList>
        #  <dxf:attrList>...</dxf:attrList>
        #  <dxf:regionList>...</dxf:regionList>
        #</dxf:part>
        
        part = {}
        #      { 'name' : None, 'type': None, 'node': Node,
        #        'xref': Node, 'attr': Node, 'region': Node }

        # name
        nml = pdom.xpath( './@name', namespaces = self.ns)
        if nml:
            part['name'] = nml[0]
            
        # type 
        tpl = pdom.xpath( './dxf:type', namespaces = self.ns)
        if tpl:
            part['type'] = self.__parseType( tpl[0] )

        # xref 
        xrl = pdom.xpath( './dxf:xrefList/dxf:xref', namespaces = self.ns)
        if xrl:
            part['xref'] = []
            for x in xrl:
                part['xref'].append( selt.__parseXref( x ) )

        # attr 
        atl = pdom.xpath( './dxf:attrList/dxf:attr', namespaces = self.ns)
        if atl:
            part['attr'] = []
            for a in atl:
                part['attr'].append( self.__parseAttr( a ) )

        # region 
        rgl = pdom.xpath( './dxf:regionList/dxf:region', namespaces = self.ns)
        if rgl:
            part['region'] = []
            for r in rgl:
                part['region'].append( self.__parseRegion( r ) )
        
        return part

    def __parseRegion( self, rdom ):
        # dummy for now
        
        return {}
