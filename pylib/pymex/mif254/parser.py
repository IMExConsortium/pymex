import sys

class Mif254Parser():
    def __init__( self, debug=False ):
        self.debug = debug

    def parse( self, file ):
        print(" Mif254Parser.parse called" )
