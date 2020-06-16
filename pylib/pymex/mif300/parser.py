import sys

class Mif300Parser():

    def __init__( self, debug=False ):
        self.debug = debug

    def parse( self, file ):
        print(" Mif300Parser.parse called" )
