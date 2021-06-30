PYMEX package is a collection of modules providing tools for accessing interaction
data distributed by The IMEx Consortium partners as well as for parsing, transformation
and construction of PSI-MI endorsed interaction data files.

## Modules
* ``pymex.xmlrecord`` - A generic, configurable XML record serializer/deserializer. 
* ``pymex.mif`` - PSI-MI XML format support (versions 2.5.4 and 3.0.0). 
* ``pymex.pypsiq`` - PSICQUC server access.

## Quick Start
```
    from lxml import etree as ET
    import pymex.mif

    rec = pymex.mif.Record()
    rec.parseMif( file, 'mif254' )
    
    for interaction in rec.interactions:
       print( "Interaction type:",interaction.type.label )
       print( "Participant count:", len(interaction.participants))
       for participant in interaction.participants:   
          print(" Participant:",participant.interactor.label)
          print("   Host:", participant.interactor.host.label)
          print("   Type:", participant.interactor.type.label)
          print("   Sequence:", participant.interactor.sequence)
    
    recDom = rec.toMif( 'mif300' )
    print( ET.tostring(recDom,pretty_print=True).decode("utf-8") )
```
### Further details: [Pymex Wiki](https://github.com/IMExConsortium/pymex/wiki)



