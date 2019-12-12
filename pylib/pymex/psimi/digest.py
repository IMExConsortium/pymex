import sys
from zipfile import ZipFile
import psimi

class PsiMiDigest():

    def __init__( self ):
        self.ns = { 'mif': 'http://psi.hupo.org/mi/mif' }
        self.xns = [ "pir", "refseq", "dip" ]
        
        
    def fopen( self, ifile ):

        source = []

        if ifile.endswith( ".zip" ):
            myzip = ZipFile( ifile, 'r' )

            for sl in myzip.namelist():
        
                # skip 'negative' interaction files
                # ( ie experiments demonstrating interaction does not happen) 
        
                if  sl.find("negative") < 0 :            
                    source.append( myzip.open( sl, 'r' ) )
        else:
            source.append( open( ifile, 'r' ) )

        return source
    
    def tabDigest( self, ifile ):
        """tabular data digest
        """
        
        src = self.fopen( ifile )
           
        header = []
        idic = {}

        mifParser = psimi.Mif254Parser()
        
        for cs in src:    
            mif = mifParser.parse( cs )
            
            if not header:

                curDepth = "N/S"
                imex = "N/S"
                pubmed = "N/S"

                if mif.pubmed is not None and len(mif.pubmed) > 0:
                    pubmed = mif.pubmed

                if mif.imex is not None and len(mif.imex) > 0:
                    pubmed = mif.imex
                
                if mif.attribute('curation depth') is not None:
                    if 'value' in mif.attribute('curation depth'):
                        curDepth = mif.attribute('curation depth')['value']
                
                header = ( "#pubmed: " + pubmed,
                           "#imex: " + imex,
                           "#curation depth: " + curDepth,
                           "#",
                           "\t".join( ("#Molecule Type",
                                       "Molecule name",
                                       "Description",
                                       "Taxon ID",
                                       "Taxon Name",
                                       "Cross-references") ) )
                
            for i in mif.irlist:
                
                iid = i.pxref['ns']+":"+i.pxref['ac']
                    
                if not iid in idic.keys():
                        
                    col = [ i.type['label'],
                            i.label,
                            i.name,
                            i.species['ac'],
                            i.species['name']]
                        
                    iln = "\t".join( col )
                        
                    xcol = [iid]
                        
                    for ns in self.xns:
                        xl =i.xref(ns)                             
                        if xl is not None and len(xl) > 0:
                            for x in xl:
                                xcol.append( x['ns'] + ":" + x['ac'] )
                                    
                    iln += '\t' +  '|'.join( xcol ) + '\n'
                                    
                    idic[iid] = iln                                
                    
        dig = '\n'.join(header) + '\n'
        for iln in idic:
            dig += idic[iln]

        return dig

    
    def dtsDigest( self, ifile, dpath='https://imexcentral.org/files/' ):
        """google data digest
        """
        src = self.fopen( ifile )

        mifParser = psimi.Mif254Parser()

        dataset = {}
        
        for cs in src:
            mif = mifParser.parse( cs )

            if not dataset: 
                dataset = { "@context":"https://schema.org/",
                            "@type":"Dataset",
                            "name": "IMEx " + mif.imex + " Interaction Dataset",
                            "description":"Biological Interaction Dataset",
                            "url":"https://imexcentral.org/icentral/imex/rec/"+ mif.imex,
                            "identifier": ["imex:"+ mif.imex],
                            "citation": "https://identifiers.org/pubmed:"+mif.pubmed,
                            "keywords":[
                                "IMEx Dataset",
                                "Biological Interactions",
                                "International Molecular Exchange Consortium"
                            ],
                            "creator":{
                                "@type":"Organization",
                                "url": "https://www.imexconsortium.org/",
                                "name":"International Molecular Exchange Consortium"
                            },
                            "distribution":[
                                {
                                    "@type":"DataDownload",
                                    "encodingFormat":"XML",
                                    "contentUrl": dpath + mif.pubmed + ".xml"
                                }
                            ]
                }
            
            mlist = []
            sdict = {}
            for i in mif.irlist:
                               
                molecule = { "name" : i.label,
                             "identifier" : i.pxref['ns']+":"+i.pxref['ac']}
                
                mlist.append(molecule)
                
                for ns in self.xns:
                    xl =i.xref(ns)
                    if xl is not None and len(xl) > 0:
                        for x in xl:
                            molecule = { "name" : i.pxref['ac'],
                                         "identifier" : i.pxref['ns']+":"+i.pxref['ac'] }
                            
                                                        
                if int(i.species['ac']) > 0:
                    species = {"name" : i.species['name'],
                               "identifier" : "taxid:" + i.species['ac'] }
                    sdict[i.species['ac']] = species
                                
            for s in sdict:
                mlist.append(sdict[s])
                                    
                #print(mlist)
                dataset['mentions'] = mlist
        
        return dataset

            
