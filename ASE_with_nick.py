from HP8560E_Spectrum_Analyser import *
import HP_Spectrum_Analyser as HP
import os
import time
import pylab
import pylab as pl
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
import stuff
import James_AFC_V1 as AFC

## import ads7_multichirper as mc
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


## # ============== WITH THE SPECTRUM ANALYSER ====================================
## [SpecAn, SpecAn_Bool] = Initialise_HP8560E_SpecAn()
## burn_time = 1*us
## rec_f = 1*GHz

AFC.spin_pump_seq(spintime = 10*s,SpecAnSweep = 'Y',rec ='Y')
## SIH.free_run_plot_window('Y', full_span = 'Y')

## burn_sequence_AWG(burn = burn_time, burn_freq, record = 'True', rec_freq = rec_f, rec_span = 50*MHz, f_name = 'ASE burn', nu = 2, sa = 'Y'):

## array = [([], 0.5*s),(['ch1'], burn_time)] + [(['ch5'], 1000*ms), (['ch2','ch4','ch5'], 100*ms)] + [(['ch2','ch5'], 100*ms)]    
## pb.Sequence(array,loop=False)
    
    
    
    
    
if __name__ =="__main__":
    
    # ============== WITHOUT SPEC AN =====================================
    #pi = range(20)
    pi = 22* us
    delay = 150*us
    #array = [(['ch1','ch3'], pi/2)] + [([''], delay)] + [(['ch1'], pi)]
    #for i in range()
    from __builtin__ import sum
    arr=  [(['ch1', 'ch3'],pi/2),([], delay), (['ch1'], pi), ([], 10*ms)]

    pb.Sequence(arr, loop = True)
    ## AFC.spin_pump_seq(spintime = 10*s,SpecAnSweep = 'N',rec ='N') #Run first   

    ## for i in range(1):
    ##     AFC.spin_pump_seq(spintime = 0.5*s,SpecAnSweep = 'N',rec ='N')
    ##     burn_time = 1*us 

    ##     array = [(['ch1','ch3'], burn_time) + ([], 100*ms)]
    ##     pb.Sequence(array,loop=False)
        
    
    
    
    
    
    
    
    
    