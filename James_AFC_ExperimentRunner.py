''' Code for various AFC experiments, runs scripts from James_AFC_V1 to preform 
    various experiments and checks'''
    
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
## import Stanford_FG as stan
import windfreakV2 as wf
import Holeburn_james_wf3 as hb
import stuff
import windfreak1_3 as wf13
import serial
import picoscope_runner as pico
import scipy.io as sci

from James_AFC_V1 import *

## import ads7_multichirper as mc

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

def ref_pulse():
    pb.Sequence([(['ch1','ch5'], 200*ms) , (['ch1','ch5','ch3'], 10*us) , (['ch5'], 50*us) , (['ch1','ch5'], 10*us) , (['ch5'],1*ms)], loop=False)
    
    
def AFC_storage_n_readout(n, bjt, burn_f, f_ext = '', record_dm1 = "False", shots = 1):
    '''
    Creates the AFC and records a number of echo shots

    n = number of teeth in comb
    bjt = burn jump time, time spent burning at each hyperfine (usually 500ms)
    burn_f = lcation of the dm -1 7/2 ~1GHz
    record_dm1 = records the AFC on the delta m = +1 transition.
    f_ext = end of each file name for data recording
    '''
    
    ###########################################################################
    #THIS STILL NEEDS TO BE SET UP FOR PB TRIGGERING (most of it is done)
    ###########################################################################
    
    
    hyperfine = '-7,2' #hyperfine level we're spin jumping to
    
    #Spin pol crystal and record background at the dm = 1 (before spin jumping)
    spin_pump_seq(spintime = 10*s, SpecAnSweep = 'N', rec = 'Y')
    if record_dm1 == "True":
        save_offset_custom(SpecAn, 5, "1.txt",freq = burn_f + 1443*MHz, span = 40*MHz, res = 30*kHz, sweep = 50*ms)
    
    #Prepare instruments pre-storage.
    #Write to the wf the freq and power needed, 
##     wf_13_cw(burn_f/1e6 + 10, -10)#Freq in MHz offset from the pulses freq.
    wf_24_cw(burn_f + 10e6, -10)#Freq offset from the pulses freq.
    
    #Set picoscope up to collect data and wait for external trigger
    ######################################################################################
    t_s = 4*ns
    r_l = 1*ms
    ps,t_sample,res = pico.run_rapid_block(Vrange = 5, n_captures = shots, t_sample = t_s, record_length = r_l)
    n_data = r_l/t_s
    ######################################################################################
    
    #Make the AFC and record AFC at dm = 1 and 0. Also record initial comb holes
    spin_jump(burn_f,state = hyperfine,rec = record_dm1, span = 10*MHz, teeth = n) 
    
    if record_dm1 == "True":
        record_dm_1(burn_f, hyperfine)
        
        
    #Set AWG to output storage pulse
    j = 5 #n*(j+2) is the waveform for the jth hyperfine (5 = -7/2) 
    mc.setWvfm(n*(j+2)+1) #so this + 1 is the waveform just after the comb creation 

    #CH3 trigger picoscope.
    #CH5 suppress carrier EOM.
    #CH1 Open RF switch for AWG.
    for i in range(shots):
        storage_arr = [(['ch3','ch5'], 1*us,WAIT),(['ch1','ch5'], 10*us),(['ch5'], 1*ms)]
#        storage_arr = [(['ch3','ch5'], 1*ms),(['ch7','ch5'], 1*ms),(['ch5'], 9*ms)]
        pb.Sequence(storage_arr, loop= False)
        
        
    #Get data from picoscope
    data = pico.get_data_from_rapid_block(ps)
    t = np.arange(data.shape[1])*t_s
    data_total = np.vstack([t,data])
    data_total = data_total.T
        
    #Save formatted data.
    file_name = time.strftime("C:\Users\Milos\Desktop\James\\" + "%Y-%m-%d Pico " + f_ext + '.mat')

    
    sci.savemat(file_name, {'data': data_total})
    plt.plot(t,data[0,:])
    plt.show()
    ps.close()
    

    
def AFC_make_n_image():
    ''' Makes and images the AFC on both the dm 0 and +1 transitions '''
    #Spin polarise
    spin_pump_seq(spintime = 10*s, SpecAnSweep = 'N', rec = 'Y')
    #Create background recording where the dm=1 is
    save_offset_custom(SpecAn, 5, "1.txt",freq = burn_f + 1443*MHz, span = 40*MHz, res = 30*kHz, sweep = 50*ms)
    #Spinjump down to -7/2 and image
    spin_jump(burn_f,state = '-7/2',rec = 'True', span = 10*MHz, teeth = n)  
    #Image dm = 1
    record_dm_1(burn_f, hyperfine)


    
def spinjump_test(n, jump_time, burn_f, hyperfine = '-7,2', f_ext='', sp = 10*MHz):
    ''' Use this code to spin jump to a particular hyperfine and record the resulting
        comb that 'should' be there
    '''
    spin_pump_seq(spintime = 10*s, SpecAnSweep = 'N', rec = 'Y')
    spin_jump(burn_f,state = hyperfine,rec = 'True', span = sp, teeth = n, f_ext = f_ext, bjt = jump_time) 
    
    
    
def spin_pol_n_see(GUI = True):
    ''' Try spin polarising, option for GUI updating SpecAn graph ''' 
    spin_pump_seq(spintime = 10*s, SpecAnSweep = 'Y', rec = 'Y')
    
    if GUI:
        SIH.free_run_plot_window('Y', full_span = 'Y')    
        
        
        
def test_pico():
    ''' Testing the picoscope runblock code. Plug CH7 into the picoscope'''
    
    shots = 5
    f_ext = 'TestRunIgnore'
    
    t_s = 10*us
    r_l = 10*ms
    ps,t_sample,res = pico.run_rapid_block(Vrange = 5, n_captures = shots, t_sample = t_s, record_length = r_l)
    n_data = r_l/t_s
    
    for i in range(shots):
        storage_arr = [(['ch3','ch5'], 25*us),(['ch1','ch5','ch7'], 500*us),(['ch5'], 1*ms)]
        pb.Sequence(storage_arr, loop= False)
        
    data = pico.get_data_from_rapid_block(ps)
    t = np.arange(data.shape[1])*t_s
    data_total = np.vstack([t,data])
    data_total = data_total.T
        
    #Save formatted data.
    file_name = time.strftime("C:\Users\Milos\Desktop\James\\" + "%Y-%m-%d Pico " + f_ext + '.mat')

    
    sci.savemat(file_name, {'data': data_total})
    plt.plot(t,data[0,:])
    plt.show()
    ps.close()
    
    
    
    
    
    
    
    
if __name__ == "__main__":
    spinjump_test(n=1,jump_time=500, burn_f = 1.25*GHz, hyperfine = '3,2', f_ext = '3/2 antihole', sp= 40*MHz)    
##     spin_pol_n_see(GUI=False)
##     test_pico()
   
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    