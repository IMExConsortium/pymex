class Registry():

    def __init__( self, reg ):
        self.reg = reg

    def __str__( self ):
            return self.__repr__()
        
    def __repr__( self ):

        if self.reg is None:
            return ''

        repr = [ "PSICQUC Registry" ]
        for s in sorted(self.reg):
            if self.reg[s]['active'].lower() == 'true':
                status = 'active'
            else:
                status = 'inactive'

            repr.append( " Name: %-20s Status: %s " % ( self.reg[s]['name'] ,
                                                        status ) )
            repr.append( "  Rest URL: %s " %(self.reg[s]['rurl']))
        
        return '\n'.join(repr)
        
