# -*- coding: utf-8 -*-
"""
Created on Mon Jan 29 11:44:30 2018
This code is set up for the AFC experiment and utilises code from Milos and myself,
such as holeburn_james_wf and the Hp spectrum analyzer/ pulse blaster codes
@author: James
"""
from HP8560E_Spectrum_Analyser import *
import HP_Spectrum_Analyser as HP
import os
import time
import pylab
from time import sleep
from datetime import datetime
import datetime
import binascii
import numpy as np
import matplotlib.pyplot as plt
import pulse_blaster as pb
import spectrum_image_HP8560E as SIH
import Stanford_FG as stan
import windfreakV2 as wf
import Holeburn_james_wf3 as hb
import time
## import new_1550_laser as las


Hz = 1
kHz = 10**3
MHz = 10**6
GHz = 10**9

hour = 3600
min = 60
s = 1
ms = 10**-3
us = 10**-6
ns = 10**-9

[SpecAn, SpecAn_Bool] = Initialise_HP8560E_SpecAn()
def getTrace():
    print(SpecAn.write('TRA?'))
    time.sleep(0.05);
    binary = SpecAn.read_raw()
    spec_data_temp = np.frombuffer(binary, '>u2')
    return spec_data_temp
    
    
def saveTrace(filename = ''):
    ''' Very basic, give it a file name and it will save a trace from SpecAn'''
    date_string = datetime.datetime.today().strftime('%y-%m-%d')
    
    filepath = "C:\Users\Milos\Desktop\James\\" + date_string + ' ' + filename +'.txt'
    try:
        os.remove(filename)
    except OSError:
        pass
    file = open(filepath,'w')
    
    #Write header
    SpecAn.write('CF?')
    center = float(SpecAn.read())

    SpecAn.write('SP?')
    span = float(SpecAn.read())

    file.write('Center freq: ' + str(center) + ' Span: ' + str(span) + '\n')
    SpecAn.write('RL?')
    ref_level = SpecAn.read()
    file.write('Reference Level: ' + ref_level + '\n')
    
    spec_data_temp = getTrace()
    data_db = SIH.convert2db(SpecAn,spec_data_temp)
    
    x = np.linspace(center - span/2, center + span/2, 601)
    data = np.vstack([x, data_db]).T
    np.savetxt(file, data, fmt='%.10e')
 
         
    file.close()


def run(n):
    l = []
    for k in range(n):
        l.append([time.time(),getTrace()])
    return l
    
    
if __name__ == "__main__":
##     l=[]
##     for k in range(50):
##         l.append([time.time(),getTrace()])
    pass
    #spin_pump_seq()

##     hb.run_offset(SpecAn) #Run once
##     SIH.free_run_plot_window('Y',full_span = 'Y')
    
    
    
