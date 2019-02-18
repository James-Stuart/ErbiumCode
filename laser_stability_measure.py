''' Used in conjuction with the 8GB AWG to burn a hole and then record said hole
    over a long period of time to record long term laser stability'''

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
## import ads7_multichirper as mc
from HP8560E_Spectrum_Analyser import *

Hz = 1
kHz = 1e3
MHz = 1e6
GHz = 1e9

hour = 3600
min = 60
s = 1
ms = 1e-3
us = 1e-6
ns = 1e-9

#You do have to set up the AWG seperately unfortunately
#Note, code timing is bad, t_space = 100ms is more like 300ms.
def laser_stability_measure(freq, t_space = 100*ms, t = 4*s, f_name = '', show = 'Y'):
    [SpecAn, SpecAn_Bool] = Initialise_HP8560E_SpecAn()
    SpecAn.write('ST 0.05') #Sweep Time 50ms
    n = int(t/t_space) #Amount of times scans needed
##     mc.setup(centerFreqL = freq, widthL = 10e4, sweepTimeL = 1e-4)
    
    if t_space < 50*ms:
        raise RuntimeError, "SpecAn's fastest sweep time & reset is 100ms, t_space cannot be faster."
    file = make_file(f_name)
    
    span = 5*MHz
    freq_sit = freq
    SpecAn.write('CF ' + str(freq_sit))
    SpecAn.write('SP ' + str(span))
    time.sleep(0.5)
    
    #Take Background measurement
    SIH.save_offset(10, 'n')
    
    #Burn a hole
    pb.Sequence([(['ch1'], 50*ms),(['ch2','ch4','ch5'], 1*ms)],loop=False)
    HP8560E_SpecAn_Trigger('EXT', 'CONTS', SpecAn)
    
    print "Recording for {}s at {} Hz".format(t,1/t_space)
    
    #Get raw data
    l = []
    for k in range(n):
        l.append([time.time(),getTrace(SpecAn, t_space)])
        
    HP8560E_SpecAn_Trigger('FREE', 'CONTS', SpecAn)
    
    t_init = l[0][0]
    t_arr = []
    center = []
    freq_arr = np.linspace(freq_sit - span/2,freq_sit + span/2, 601)
    
    for i in range(n):
        #Convert to dB and background subtract post data collection
        dat = SIH.convert2db(SpecAn,l[i][1])
        dat = hb.compensate(dat, span)
        #Make time and freq peak array
        t_arr.append(l[i][0]- t_init)
        index = np.argmax(dat[50:]) #The carrier also makes a hole, this should ignore it
        center.append(freq_arr[index])
        
    data = np.vstack([t_arr, center]).T
    np.savetxt(file, data, fmt='%.10e')
    

##         
    pb.Sequence([(['ch2','ch5','ch4'], 1*ms)], loop=False)
    #Plot
    if show == 'Y':
        plt.plot(t_arr,center)
        plt.show()
        
    return l,t_arr,center,data
    
    
    
    
def make_file(f = ''):
    day = time.strftime("%d")
    month = time.strftime("%m")
    year = time.strftime("%Y")
    hour = time.strftime("%H")
    minute = time.strftime("%M")
    second = time.strftime("%S")
    usec = datetime.datetime.now().strftime("%S.%f")
    
    date_string = year + '-' + month + '-' + day

    filepath = "C:\Users\Milos\Desktop\James\Laser_stability\\" + date_string + ' laser stability' + f + '.txt'
    try:
        os.remove(filepath)
    except OSError:
        pass
    file = open(filepath,'w')
    return file
    
    
    
    

def getTrace(SpecAn, t_space):
    pb.Sequence([(['ch2','ch4','ch5'],100*ms),(['ch5'],10*us)],loop=False)
    SpecAn.write('TRA?')
    time.sleep(t_space - 50*ms);
    binary = SpecAn.read_raw()
    spec_data_temp = np.frombuffer(binary, '>u2')
    return spec_data_temp
    
    
    
    
    
if __name__ == '__main__':
    for i in range(50):
        arr,t_arr,center,data = laser_stability_measure(1.3*GHz, f_name = str(i), show ='N')
        