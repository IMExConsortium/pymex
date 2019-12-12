import sys
sys.path.insert(0,"/cluster1/home/lukasz/git/psi-mi-tools/pylib")
sys.path.insert(0,"/cluster1/home/lukasz/git/dip-backend/pylib")
sys.path.insert(0,"/cluster1/home/lukasz/git/dip-proxy-tools/pylib")

import re
import io
import dippy as DP
import dipropy as DPX
import psimi
from lxml import etree as ET

class EvidSubmitter():
    def __init__( self, user='guest', password='guest',
                  mode='dev', debug=False ):

        self.dxfns = { 'dxf': 'http://dip.doe-mbi.ucla.edu/services/dxf15' }
        self.dpc = DP.Client()
        self.nsub = DP.NodeSubmitter()
        self.ssub = DP.SrceSubmitter()

    def buildDirect(self, expt ):

        evtype = self.dpc.dxf.typeDefType( ns='dxf',
                                           ac='dxf:0015',
                                           name='evidence' )
        pexptype = self.dpc.dxf.typeDefType( ns='dxf',
                                             ac='dxf:0048',
                                             name='experiment-node')
        
        mthAtt = self.dpc.dxf.attrType( ns="dxf", ac="dxf:0064",
                                        name="method",
                                        value="direct assay")
        mthAtt.value.ns = 'eco'
        mthAtt.value.ac = 'ECO:0000002'

        resAtt = self.dpc.dxf.attrType( ns="dxf", ac="dxf:0065",
                                        name="result")
        
        for att in expt.attrList.attr:
            # link type, reslut
            if att.ac in ['dip:0001','dxf:0050']:
                resAtt.value = att.value
                resAtt.value.ns = att.value.ns
                resAtt.value.ac = att.value.ac
                
        pexpt = self.dpc.dxf.partType( type = pexptype,
                                       node = expt,
                                       name = '',
                                       id = 1 )
                
        evnode = self.dpc.dxf.nodeType( id = 1,
                                        ns='dip',
                                        ac= '',                                        
                                        type=evtype,
                                        label = '',
                                        name = '',
                                        attrList = {'attr':[mthAtt, resAtt]},
                                        partList = {'part':[pexpt]})
        
        return evnode
