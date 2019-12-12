import sys
import json

import dxf as DXF
from lxml import etree as ET

class DXF15Node():
    """  Representation of a DXF15 node.
    """
    def __init__( self, dxf, root=None ):
        self.nsp = { 'dxf': 'http://dip.doe-mbi.ucla.edu/services/dxf15' }
        self.nsmap = {None: self.nsp['dxf'] }
        self.dxfp = "{%s}" % self.nsp['dxf']
        
        self._root = root
        self._dxf = dxf
        
    @property
    def root( self ):
        return self._root

    @property
    def dom( self ):
        return self._root

    @property
    def dxf( self ):
        return self._dxf

    @property
    def dxfstr( self ):
        (ndom,id) = self.dxfdom();        
        #print(ET.tostring( ndom, encoding='utf-8').decode('utf-8'))

    @property
    def ns( self ):
        return self._dxf['ns']

    @property
    def ac( self ):
        return self._dxf['ac']

    @property
    def label( self ):
        if 'label' in self._dxf:
            return self._dxf['label']
        else:
            return ""

    @property
    def name( self ):
        if 'name' in self._dxf:
            return self._dxf['name']
        else:
            return ""
        
    @property
    def type( self ):
        return self._dxf['type']

    @property
    def xref( self ):
        if 'xref' in  self._dxf.keys():
            return self._dxf['xref']
        else:
            return []

    @property
    def attr( self ):
        if 'attr' in  self._dxf.keys():
            return self._dxf['attr']
        else:
            return []
        
    @property
    def part( self ):
        if 'part' in  self._dxf.keys():
            return self._dxf['part']
        else:
            return []
        
    def __str__(self):
        return self.__repr__()
    
    def __repr__(self):        
        rep=[]
        rep.append("  Node:")

        nsac = "   (NS):AC:\t"
        if self.ns is not None:
            nsac += "(" + self.ns + "):"
        else:
            nsac += "(N/A)"
        if self.ac is not None:
            nsac += self.ac
        else:
            nsac += "N/A"            
        rep.append(nsac)

        if self.label is not None:
            rep.append( "   Label:\t" + str(self.label))
        else:            
            rep.append( "   Label:\tN/A" )

        if self.name is not None:
            rep.append( "   Name:\t" + str(self.name))
        else:            
            rep.append( "   Name:\tN/A" )

        if self.type is not None:            
            rep.append("   Type:\t" + str(self.type) )
            
        if self.xref is not None:
            rep.append( "   Xrefs:" )
            for x in self.xref:
                rep.append("    " + str(x) )

        if self.attr is not None:
            rep.append( "   Attributes:" )
            for a in self.attr:
                rep.append("    " + str(a) )

        if self.part is not None:
            rep.append( "   Parts:" )
            for p in self.part:
                rep.append("    " + str(p) )
                    
        return '\n'.join(rep)

    def dxfdom( self, parent = None, id = None ):
        
        if parent is None:
            ndom = ET.Element( self.dxfp + "node", nsmap = self.nsmap) 
        else:            
            ndom = ET.SubElement( parent, self.dxfp + "node" )

        if id is None:
            id = 1
        else:
            id+=1

        ndom.attrib['id']= str( id )
        ndom.attrib['ns']= str( self.ns )
        ndom.attrib['ac']= str( self.ac )

        lb0 = ET.SubElement( ndom, self.dxfp + "label" )
        if self.label is not None:            
            lb0.text=self.label
        else:
            lb0.text=""

        nm0 = ET.SubElement( ndom, self.dxfp + "name" )
        if self.name is not None:
            nm0.text=self.name
        else:
            nm0.text=""

        #<type>...</type>
            
        if self.type is not None:
            tp0 = self.typedom( self.type, parent = ndom )

            
        #<xrefList>
        # <xref>...</xref>
        #</xrefList>
            
        if self.xref is not None and len(self.xref) > 0:                    
            xrl0 = ET.SubElement( ndom, self.dxfp + "xrefList" )
            for x in  self.xref:
                xr0 = self.xrefdom( x, parent = xrl0 )
                
                
        #<attrList>
        # <attr>...</attr>
        #</attrList>
                    
        if self.attr is not None and len(self.attr) > 0:
            atl0 = ET.SubElement( ndom, self.dxfp + "attrList" )
            for a in self.attr:
                at0 = self.attrdom( a, parent = atl0 )

                
        #<partList>
        #   <part id="3" name="CEG1{A}">
        #      <type name="linked-node" ac="dxf:0010" ns="dxf"/>
        #      <node>...</node>
        #   <part>
        # </partList>                                                                          

        if self.part is not None and len(self.part) > 0:
            prl0 = ET.SubElement( ndom, self.dxfp + "partList" )
            pid = 1
            for p in self.part:
                pt0 = ET.SubElement( ptl0, self.dxfp + "part" )
                pt0.attrib['id'] = pid
                pt0.attrib['name'] = p['name']

                if 'type' in p:
                    ptp0 = self.typedom( p['type'], parent = pt0 )
                
                if 'node' in p:
                    pnd0 = DXF.DXF15Node( p['node'] ).dxfdom( parent = pt0 )

                if 'xref' in p:
                    if p['xref'] is not None and len(p['xref']) > 0:
                        xrl0 = ET.SubElement( pt0, self.dxfp + "xrefList" )
                        for x in  p['xref']:
                            xr0 = self.xrefdom( x, parent = xrl0 )                             
                            
                if 'attr' in p:
                    if p['attr'] is not None and len(p['attr']) > 0:
                        atl0 = ET.SubElement( pt0, self.dxfp + "attrList" )
                        for a in  p['attr']:
                            at0 = self.xrefdom( a, parent = atl0 )                             
                                    
                if 'feature' in p:
                    if p['feature'] is not None and len(p['feature']) > 0:
                        ftl0 = ET.SubElement( pt0, self.dxfp + "featureList" )
                        for f in  p['feature']:
                            ft0 = self.regiondom( f, parent = ftl0 )                   
            pid += 1        
        return (ndom, id)

    def typedom( self, tpe, parent = None):
        if parent is None:
            tp0 = ET.Element( self.dxfp + "type", nsmap = self.nsmap) 
        else:
            tp0 = ET.SubElement( parent, self.dxfp + "type" )
            
        tp0.attrib['name'] = tpe['name']
        tp0.attrib['ns'] = tpe['ns']
        tp0.attrib['ac'] = tpe['ac']
        if 'node' in tpe:
            tpn0 = DXF.DXF15Node( tpe['node'] ).dxfdom( parent = tp0 )

        return tp0

    def xrefdom( self, xref, parent = None ):

        #<xref type="produced-by" typeAc="dxf:0007" typeNs="dxf"
        #       ac="4932" ns="TaxId">
        #  <node>...</node>
        #</xref>

        if parent is None:
            xr0 = ET.Element( self.dxfp + "xref", nsmap = self.nsmap) 
        else:
            xr0 = ET.SubElement( parent, self.dxfp + "xref" )
        
        xr0.attrib['ns'] =  xref['ns']
        xr0.attrib['ac'] =  xref['ac']
        if 'type' in xref:
            xr0.attrib['type'] =  xref['type']
        if 'typeNs' in xref:
            xr0.attrib['typeNs'] = xref['typeNs']
        if 'typeAc' in xref:
            xr0.attrib['typeAc'] = xref['typeAc']
                    
        if 'node' in xref:
            xrn0 = DXF.DXF15Node( xref['node'] ).dxfdom( parent = xr0 )                    


    def attrdom( self, attr, parent = None ):

        #  <attr name="link-type" ac="dip:0001" ns="dip">
        #   <value ac="MI:0218" ns="psi-mi">
        #     physical interaction
        #   <value>
        #   <type> ...</type>
        #   <node>...</node> 
        #  <attr>
        
        if parent is None:
            at0 = ET.Element( self.dxfp + "attr", nsmap = self.nsmap) 
        else:
            at0 = ET.SubElement( parent, self.dxfp + "attr" )

            at0.attrib['name'] = attr['name']
            at0.attrib['ns'] = attr['ns']
            at0.attrib['ac'] = attr['ac']
            if 'value' in attr:
                val = attr['value']
                if 'value' in val:
                    atv0 = ET.SubElement( at0, self.dxfp + "value" )
                    atv0.text = val['value']
                                                  
            if 'type' in attr:
                atp0 = self.typedom( attr['type'], parent = at0 )
                    
            if 'node' in attr:
                atn0 = DXF.DXF15Node( attr['node'] ).dxfdom( parent = at0 )                    
       
        return at0 

    
    def featuredom( self, regn, parent = None ):
        
        if parent is None:
            rg0 = ET.Element( self.dxfp + "feature", nsmap = self.nsmap ) 
        else:
            rg0 = ET.SubElement( parent, self.dxfp + "feature" )

        return rg0
