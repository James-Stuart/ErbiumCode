#############BASIC FUNCTIONS OF THE BURLEIGH WA-7600 Wavemeter#################
##############################MILOS RANCIC 2014################################

import sys
from numpy import *
from ctypes import *
from time import clock
from visa import *
from struct import *
rm = ResourceManager()

def Initialise_Burleigh_WM():
    
    #This creates the intrument handle for the Burleigh wavemeter to talk to the spectrum analyser
    #Burleigh_WM = SerialInstrument("COM4", term_chars = CR)
    Burleigh_WM = rm.open_resource("GPIB::4")
    Burleigh_WM.write("*IDN?")
    print ""
    print "-you are using the:" + Burleigh_WM.read()
        
    #generates a boolean to say that its been initialise
    Burleigh_Bool = 1
    
    return(Burleigh_WM, Burleigh_Bool)
