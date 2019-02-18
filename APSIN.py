#======================================================
# APSIN 6010 HC Initialiser ||  James 2017
#======================================================

import sys
from numpy import *
from ctypes import *
from time import clock
from visa import *
from struct import *
rm = ResourceManager()

def initialise():
    initialse_machine = rm.open_resource('USB0::0x03EB::0xAFFF::111-233500400-0489::INSTR')
    initialse_machine.write('*IDN?')
    thing = initialse_machine.read()
    print thing
    
    
initialise()