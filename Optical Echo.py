
import pulse_blaster_Milos as pb
from Stanford_FG import *
import numpy as np
import binascii
import os
import pylab
from Tektronix_TDS540A import *
import matplotlib.pyplot as plt
import time
import unicodedata
from Agilent_OSA import *

#some usefull constants
Hz = 1
kHz = 10**3
MHz = 10**6
GHz = 10**9

ns = 10**-9
us = 10**-6;
ms = 10**-3;
s = 1;


global Stanford_Bool
global Stanford_FG

def save_data(filename, folder_name,  laser_wavelength, CH1, CH2, timebase):
    
    
    
    day = time.strftime("%d")
    month = time.strftime("%m")
    year = time.strftime("%Y")
    hour = time.strftime("%H")
    minute = time.strftime("%M")
    second = time.strftime("%S")
    
    date_string = day + "_" + month + "_" + year
    time_string = hour + "Hrs " + minute + "Mins " + second + "Secs"
    
    filepathA = "C:\Users\Milos\Desktop\EIT Data\\" + date_string

    if not os.path.exists(filepathA):
        os.mkdir(filepathA)
        
    filepathB = "C:\Users\Milos\Desktop\EIT Data\\" + date_string + "\\" + folder_name

    if not os.path.exists(filepathB):
        os.mkdir(filepathB)
        

        
    location = filepathB + "\\" + filename + ".txt"
    OutputFile = open(location, 'w')
    OutputFile.write("The Date is: " + date_string + "\n")
    OutputFile.write("The Time is: " + time_string + "\n")
    OutputFile.write("The laser wavelength is: " + str(laser_wavelength) +  " nm \n")
    OutputFile.write(str(laser_wavelength)+"\n")
    OutputFile.write("The Time unit is:" + str(timebase) +  "seconds \n")
    OutputFile.write(str(timebase)+"\n")

  
    
    for i in range(len(CH1)):
        OutputFile.write(str(CH1[i]) + ",  " 
        + str(CH2[i])+ "\n")



#



#[Stanford_FG, Stanford_Bool] = Initialise_Stanford_FG()

#input stanford parameters for VCO burn (0.865 to 2.334 GHz). each section corresponds to one sweep section
#sweep_array = np.array([[1.3*GHz, 2.3*GHz, 600*ms]])
#VCO_Sweep_backwards(sweep_array, Stanford_FG, Stanford_Bool)


Scope = Initialise_Tektronix_540D()
[Agilent_OSA, Agilent_OSA_bool] = Initialise_OSA()
laser_wavelength = OSA_measure_wavelength(Agilent_OSA)

for j in range (1, 20):
    for i in range(1, 30):
        pulse_delay = 200*j
#

        pb.Sequence([(['ch1'], 3*s),  
                    (['ch1', 'ch2', 'ch4'], 0.75*us),                           #pi/2 pulse the anti hole
                    ([],pulse_delay*us),                                       #wait fore dephasing
                    (['ch1', 'ch2','ch4'], 1.5*us),                      
                    ([],(pulse_delay-10)*us),                                       #wait for rephasing
                    (['ch7','ch6'], 60*us),        #switch light to carrier, turn on weak probe and trigger scope 
                    (['ch7'], 1*ms)],
                    loop=False)
#have to wait for the pulse blaster sequence to finish before we collect the data, couldnt figure out a smarter way to do this using
#interrupts.....scope behaves strangly

        print 'delay is: ' + str(pulse_delay)
        print 'run number ' + str(i)
        time.sleep(4)


s
        [CH1, CH4, unicodetime] = collect_scope_trace(Scope)

        #need to convert scope timebase into float, also, the scope counts in divisions of 50 units, so need to divide by 50 to get actuall time base
        timebase = float(unicodetime)
        timebase = timebase/50

        filename = str(pulse_delay*2) + ' us total delay, Run ' + str(i)
        folder_name = 'Optical Echoes, Transition 8 to 8'
        save_data(filename, folder_name,  laser_wavelength, CH1, CH4, timebase)

