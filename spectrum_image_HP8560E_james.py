import sys
from ctypes import *
import time
import matplotlib.pyplot as plt
import matplotlib.widgets as widget
from visa import *
from struct import *
from Arduino_Pulseblaster_SpecAn_Trench import *
from Rigol_DMM import *
from Burleigh_Wavemeter import *
from HP8560E_Spectrum_Analyser import *
from Stanford_FG import *
from Agilent_OSA import *

import pulse_blaster as pb
import numpy as np
import binascii
import os
import pylab

from matplotlib.widgets import CheckButtons
#Copying Milos's code

#some usefull constants
Hz = 1
kHz = 10**3
MHz = 10**6
GHz = 10**9

ns = 10**-9
us = 10**-6
ms = 10**-3
s = 1


#here we generate a handle for the spectrum analyser, turn on the RF and
#set it to trigger internally
global SpecAn_Bool
global SpecAn

#global Burleigh_WM_Bool
#global Burleigh_WM

[SpecAn, SpecAn_Bool] = Initialise_HP8560E_SpecAn()

def move_center(offset = 0,text = False):
    #Finds local minimum, moves marker some "halfway" frequency away from minimum
    #Sets marker to be the new center frequency along with moving the marker
    #Print the new center frquency
    SpecAn.write("MKMIN")
    SpecAn.write("MKF?")
    center_freq = SpecAn.read()
    
    halfway = offset*kHz
    center_freq = float(center_freq)
    center = center_freq + halfway
    center_string = "CF " + str(center)
    SpecAn.write(center_string)
    SpecAn.write("MKF " + str(center))
    
    if text == True:
        print("Center frequency set to " + str(center) + " Hz. " + str(halfway) + 
        " Hz from the local minima.") 
    
    return
    
def set_zero_span():
    SpecAn.write("SP 0")
    return
    
    
#move_center()
    
    