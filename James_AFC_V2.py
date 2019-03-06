# -*- coding: utf-8 -*-
"""
Created on Tue Mar  5 13:28:59 2019
James_AFC_V2. AFC for quantum AFC measurements.
This is going to require a lot of re-writting old code... ohh boy.
@author: James
"""

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
import windfreak1_3 as wf13
import serial
import picoscope_runner as pico
import scipy.io as sci
import rigolfg as rigolfg
import purephotonicscontrol.ITLA_Wrap as ITLA_Wrap

import ads7_multichirper as mc
## import new_1550_laser as las

#Pulse blaster commands
WAIT = 8 #From the Pulseblaster code. for telling Pb to wait for trigger
LOOP = 2
END_LOOP = 3


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

def multi_record(SpecAn,d_time,n,filepath):
    
    '''Takes 'n' scans on the HP Spectrum Analyzer at ~d_time intervals.
       This is an augmented version of record_trace from holeburn_james.
       Also records the times for each data recording event.'''
    #Run the following first to set up the text file.
    #hb.create_file(SpecAn, filename = '', compensated = 'N', sweep_again = 'Y', n=1, burn_time = '')

    SpecAn.write('SP?')
    span = float(SpecAn.read())  
    SpecAn.write('CF?')
    center = float(SpecAn.read())   
     
    file = open(filepath,'a')
    x = np.linspace(center - span/2, center + span/2, 601)
    spec_data_db = np.zeros((601,n))
    
    record_time = []
    for i in range(n):
        SpecAn.write('TS')
        #Waits for Spectrum Analyser to finish Data sweep
        SpecAn.wait_for_srq(timeout = 5000)

      
        #Gets the trace from the SpecAn
        SpecAn.write('TRA?')
        binary = SpecAn.read_raw()
        spec_data_temp = np.frombuffer(binary, '>u2') # Data format is big-endian unsigned integers
        
        record_time.append(datetime.now().strftime("%H:%M:%S.%f"))
        
        
        spec_data_db[:,i] = SIH.convert2db(SpecAn,spec_data_temp)
        
        if compensated == 'Y':
            spec_data_db[:,i] = compensate(spec_data_temp, span)
        
        SpecAn.write("CLEAR; RQS 4")
        pb.Sequence([(['ch2','ch5'],d_time)],[(['ch2','ch5','ch4'],1*ms)],loop=False)
    
    #Conjoins both x and spec_data_temp vectors and saves them to file     
    data = np.vstack([x, spec_data_db]).T
    np.savetxt(file, data, fmt='%.10e')
     
             
    file.close()
    pylab.ion()
 
    if sweep_again == 'Y':
        HP8560E_SpecAn_Trigger("FREE", 'CONTS', SpecAn)
        
    return x, spec_data_db, filepath        
#

#
def spin_pump_seq(spintime = 10*s,SpecAnSweep = 'Y',rec ='Y'):
    ''' For spin polarizing the crystal.
        Triggers pulseblaster CH6 on - off, changes the state of the mems switch 
        which lets the photonics laser to sweep over the dm = 1 & 2 for a given time, default 10s
        Then allows for the recording of the Spin pumped spectrum if rec 'Y'
    '''
    #Toggle the mems switch for n sec
    if rec == 'Y':
        HP8560E_SpecAn_Trigger('FREE', 'CONTS', SpecAn)
        SpecAn.write('CF ' + str(1.45*GHz))
        SpecAn.write('SP ' + str(2.90*GHz))
    
    pb.mems_switch_toggle(spintime,n=1,other_ch='',init_state = 1)
    sleep(spintime)
    
    #Record full span spectrum, else: just toggle the mems switch again 
    if rec == 'Y':
        filepath = hb.create_file(SpecAn, compensated = 'Y', n=1, burn_time = 0, filename = ' Spin pumped')
        sleep(100*ms)
        pb.Sequence([   (['ch5'], 0.5*s),
                        (['ch5', 'ch6'], 20*us), (['ch5'], 5*ms),
                        (['ch2','ch4','ch5'], 50*ms), #RF Switch, Trigger SpecAn, EOM Bias on 
                        (['ch2','ch5'], 100*ms),
                        ], loop=False)
        hb.record_trace(SpecAn, filepath, filename = ' Spin pumped', compensated = 'Y', sweep_again = SpecAnSweep, n=1, burn_time = '')
    else:
        pb.Sequence([(['ch5', 'ch6'], 20*us), (['ch5'], 5*ms),
                        ], loop=False)
#

#
def spin_jump(freq,state = '3,2',rec = 'True', span = 20*MHz, teeth = 1, f_ext ='', bjt = 500, rec_offs = True):
    ''' Sets the 8GB AWG to a given frequency and burns a 100kHz hole, gives the option to 
        record the anti-hole created.
        Then burns on top of the anti-hole with a larger chirp 500 kHz - 2 MHz 
        rec_offs if you want a new background measurement
        '''
    #Splittings are [107.64, 110.42,105.17,92.34,73.02,47.94]
    #delta m = -1 energy gaps 7/2 -> -7/2: [0, -107.64, -218.06, -323.23, -415.57, -488.59, -536.53]+some offset
    state_dict = {'3,2': 0,'1,2': 1,'-1,2': 2,'-3,2': 3,'-5,2': 4,'-7,2': 5}

    if state not in state_dict: #Check if variable state is valid
        print('Error, variable state must be in [3,2 ... -7,2]')
        
    print("Initial burn on the Delta m = -2")
    target_state = state_dict[state]
    
    #I am keeping the -107.64 to allow the ability to image the 5/2> easily
    #DELTA M=-2 |7/2> location is -903.02MHz
    e_gap = np.array([-107.60, -218.09, -323.2, -415.50, -488.20, -535.89, 460.99])*MHz #Gaps in hyperfine energy levels
##     e_gap = np.array([0, -107.60, -218.09, -323.2, -415.50, -488.20, -535.89, 460.99])*MHz #GUse this if you want to look at one hyperfine higher
##     e_gap = np.array([1685.0, 1603.5, 1530.0, 1472.2, 1436.3, 1428.8, 1453.5])*MHz #Use this to look at dm = 1
##     e_gap = np.array([1557, 1557, 1557, 1557, 1557, 1557, 1557])*MHz #Set span to 270MHz and use this to image the entire DM = 1
    #From 7/2 - 5/2 -> -5/2 - -7/2 (have the image the -7/2> on the Delta m = 0
    str_name = [' 3,2 antihole',' 1,2 antihole',' -1,2 antihole',
    ' -3,2 antihole',' -5,2 antihole',' -7,2 antihole']
    
    #Perform the first burn (which should have a narrower chirp and quicker burn time
    n = teeth
    if target_state >= 0:
        mc.setWvfm(0,teeth-1)
        burn_sequence_AWG_cust(burn = 100*ms, burn_freq= freq, record = 'False', rec_span = span, f_name = ' ' + f_ext + ' 7,2 hole', sa = 'N')# ' + str(i))
    
    #Perform the rest of the spin jump down to the desired level.
    #Cant look at the anti-hole in each level though
    j = target_state
    if target_state >= 0:
        #This part here is ugly and weird. Maybe ill fix it properly one day.
        if target_state == 0:
            mc.setWvfm(0,teeth-1) #Jumps the comb from the |3/2> to the |-7/2>
        else:
            mc.setWvfm(0,teeth*(j+1)-1) #Jumps the comb from the |3/2> to the |-7/2>
##             mc.setWvfm(0,teeth*(j+2))  #For Comb clean up.
        burn_sequence_AWG_cust(burn = bjt*ms*(j+1), burn_freq= freq, record = rec, rec_freq = freq+e_gap[j+1], rec_span = span, f_name = ' ' + f_ext + str_name[j], sa = 'N', rec_offs = rec_offs)
    

    #SIH.free_run_plot_window('Y',full_span = 'Y')
    
#def spin_jump_dmneg1, is in JAMES_AFC_V1
#def spin_jump_time_measurement(freq, times, state = '5,2'):, IS IN JAMES_AFC_V1
#def spin_jump_time_measurement_faster(times, burn_f, state = '5,2'):, IS IN JAMES_AFC_V1
#
def burn_sequence_AWG(burn, burn_freq, record = 'True', rec_freq = '', rec_span = 10*MHz,
                      f_name = '', nu = 2, sa = 'Y'):
    
    ''' Copy of the burn sequence function from Holeburn james wf3,
        but uses the 8GB AWG instead of the WF as the burner'''
        
    filepath = ''
    if rec_freq == '':
        rec_freq = burn_freq
    
    if record == 'True':
        filepath = hb.create_file(SpecAn, n=1, burn_time = burn, filename = f_name)
        hb.run_offset(SpecAn, freq = rec_freq, span = rec_span, res = 30*kHz, sweep = 50*ms,
                      full_span = 'N', show_window = 'N',n = nu)
        
    
    pb.hole_burn(burn)
    
    if record == 'True':
        filepath=hb.record_trace(SpecAn, filepath, compensated = 'Y', sweep_again = sa, burn_time = burn)
    sleep(0.5*s)


    hb.full_sweep(SpecAn)
    
def burn_sequence_AWG_cust(burn, burn_freq, record = 'True', rec_freq = '', rec_span = 10*MHz,
                           f_name = '', nu = 2, sa = 'Y', rec_offs = True, opt_bac = 'offs1.txt'):
    
    ''' Same as burn_sequence_AWG, but uses save custom offset rather than hb.run_offset '''
        
    filepath = ''
    if rec_freq == '':
        rec_freq = burn_freq
    
    if record == 'True':
        filepath = hb.create_file(SpecAn, n=1, burn_time = burn, filename = f_name)
        if rec_offs:
            save_offset_custom(SpecAn, 5, 'offs1.txt', freq = rec_freq, span = rec_span, res = 30*kHz, sweep = 50*ms)
        else:
            SpecAn.write("CF " + str(rec_freq))
            SpecAn.write("SP " + str(rec_span))        
    
    arr1 = [([], 0.5*s),(['ch1'], burn)] + [(['ch5'], 100*us), (['ch2','ch4','ch5'], 100*ms)] + [(['ch2','ch5'], 100*ms)]
    pb.Sequence(arr1,loop=False)
##     pb.hole_burn(burn)
    
    if record == 'True':
        filepath=hb.record_trace(SpecAn, filepath, compensated = 'Y', sweep_again = sa, burn_time = burn, opt_bac = opt_bac)
    sleep(0.5*s)


    hb.full_sweep(SpecAn)

#

#
def record_dm_1(freq, f_ext = '', tn = 3):
    ''' Set up to record the anti-holes made by spin jumping by looking at three places
    on the Delta m = 1 '''
    if freq > 1210*MHz:
        print('WARNING: Freq set too high, might not be able to see the |5/2> on the Delta m = 1')
    
    rec_freq = np.array([1557*MHz,1472*MHz,1529*MHz])+freq
    span = np.array([270,20,20])*MHz
    f_name = [' ' +f_ext + ' dm1',' ' +f_ext + ' dm 12',' ' + f_ext + ' dm13']
    opt = ["C:\\Users\\Milos\Desktop\\Er_Experiment_Interface_Code\\1.txt",
        "C:\\Users\\Milos\Desktop\\Er_Experiment_Interface_Code\\2.txt",
        "C:\\Users\\Milos\Desktop\\Er_Experiment_Interface_Code\\3.txt"]
  
    
    for i in range(1):
        SpecAn.write('SP ' + str(span[i]))
        SpecAn.write('CF ' + str(rec_freq[i]))
        sleep(0.01)
        filepath = hb.create_file(SpecAn, n=1, burn_time = 1*ms, filename = f_name[i])
        pb.Sequence([([], 0.5*s)] + [(['ch5'], 1000*ms), (['ch2','ch4','ch5'], 100*ms)] + [(['ch2','ch5'], 100*ms)],loop=False)
        filepath=hb.record_trace(SpecAn, filepath, compensated = 'Y', sweep_again = 'N', burn_time = 1*ms, opt_bac = opt[i])
        sleep(0.05)
        
    
    
#

#
def save_offset_custom(SpecAn, avg_num, save_file, freq, span = 40*MHz, res = 30*kHz, sweep = 50*ms):
    SpecAn.write("CF " + str(freq))
    SpecAn.write("SP " + str(span))
    SpecAn.write("RB " + str(res))
    SpecAn.write("ST " + str(sweep))
    #Give time to let the SpecAn change span settings
    sleep(0.1)
    
    SpecAn.write("SRCPWR?")
    SpecAn_Power = SpecAn.read()
    print("Power is: " + str(SpecAn_Power))
    
    #Traces are made up of 601 points (x axis) with a value from 0 to 610
    #This can be converted into dB
    SpecAn.write('LG?')
    dB_div = float(SpecAn.read())
    entire_depth = 10*dB_div #how many dB in the entire display
    SpecAn.write('RL?') #Get the reference level
    ref_level = float(SpecAn.read())
    
    lowest_point = ref_level - entire_depth 
    #To convert Y data to dB -> y_data*entire_depth/610 + lowest_point
    
    offset_array = np.zeros((avg_num,601),dtype=float)
    HP8560E_SpecAn_Trigger('EXT', 'CONTS', SpecAn)
##     pb.Sequence([(['ch2','ch5','ch4'], 1*ms)], loop=False)
    
    #Leave enough time for it sweep and store a new trace
##     sleep(0.4)
##     [SpecAn_track, SpecAn_Power] = HP8560E_SpecAn_RF(tracking_gen, RF_power, SpecAn)
    #now we collect the data trace
    for i in range(avg_num):
        
        pb.Sequence([(['ch2','ch5','ch4'], 1*ms)], loop=False)
        sleep(sweep+0.2)
        SpecAn.write("TRA?")
        binary_string = SpecAn.read_raw()
        hex_string = binascii.b2a_hex(binary_string)
        offset_data_temp = np.zeros(601)
        
        for j in range (601):
            
            offset_data_temp[j] = int('0x' + hex_string[j*4: j*4+4], 0)
        offset_array[i,:] = offset_data_temp[:]
        
        time.sleep(0.07)

    avg_offset_data = np.average(offset_array,0)
    avg_offset_data = avg_offset_data*entire_depth/610 + lowest_point #Convert to dB
    np.savetxt(save_file, avg_offset_data,fmt='%.10e',delimiter=",")
#

#
def reference_pulse(f_ext = '', voltRange = 0.2):
    ''' Spin polarize the crystal and send a pulse through at the freq where the AFC
    would be. Needs to know the number of teeth to know which bit of memory the pulse is stored at.'''
    
    mc.setWvfmKey('Pulse')
    AWG_trig_out(1)

    #Set picoscope up to collect data and wait for external trigger
    t_s = 4*ns
    r_l = 20*us
    t_sample,res = pico.run_rapid_block(ps, Vrange = voltRange, n_captures = 1, t_sample = t_s, record_length = r_l)
    n_data = r_l/t_s
    
    print("Toggling MEMS switch high for 10 s")
    pb.Sequence([(['ch5'], 0.5*us), 
    (['ch5','ch6'], 10), #Spin polarise crystal
    (['ch5'], 0.5*us, WAIT), 
    (['ch5'], 49.5*us),
    (['ch3','ch5'], 0.5*us), 
    (['ch1','ch5'],50*us), 
    (['ch5'], 1*ms)] ,loop=False,bStart=False)
    sleep(11)
    
    #Old Sequence
##     pb.Sequence([(['ch5'], 0.5*us), (['ch5'], 0.5*us, WAIT), (['ch5'], 49.5*us),
##     (['ch3','ch5'], 0.5*us), (['ch1','ch5'],1*ms), (['ch5'], 1*ms)] ,loop=False,bStart=False)
    #CH3 to picoscope (start recording just before pulse arrives), 
    #CH1 to open RF switch for AWG, 
    #CH5 so carrier sideband beat on laser is strong
    sleep(0.1)
    #AWG_trig_out(0)

    #sleep(1)
    data = pico.get_data_from_rapid_block(ps)
    t = np.arange(data.shape[1])*t_s
    data_total = np.vstack([t,data])
    data_total = data_total.T
    
    
##     for dat in data_total[0]:
##         if dat == "inf" or dat == "-inf":
##             raise RuntimeError, "Picoscope V range too small"
    
    #Save formatted data.
    file_name = time.strftime("C:\Users\Milos\Desktop\James\\" + "%Y-%m-%d REFERNCE Pico " + f_ext + '.mat')

    
    sci.savemat(file_name, {'Vrange': voltRange,'sampleRate': t_s,'data': data_total})
    
    

#













#
def make_AFC(burnf, AFCparameters, recComb = False, f_ext = ''):
    '''
    Makes an AFC for the quantum AFC experiment
    burnf = frequency offset from the laser to the delta m = -1 peak
    AFCparameters = [n, bjt]. n, number of teeth. BJT, burn jump time (time spent on each hyperfine)
    '''
    n = AFCparameters[0]
    bjt = AFCparameters[1]
    hFinal = '-7,2' #Change this is you wish to make a comb at a different hyperfine
    
    
    #Spin polarise the crystal
    spin_pump_seq(spintime = 10*s, SpecAnSweep = 'N', rec = 'Y')   
    
    
    if recComb:
        save_offset_custom(SpecAn, 5, "1.txt",freq = burn_f + 1443*MHz, span = 40*MHz, res = 30*kHz, sweep = 50*ms)
    #Spin just a comb
    spin_jump(burn_f, state = hFinal, rec = record, span = 20*MHz, teeth = n, bjt=bjt, f_ext=f_ext) 
    if recComb:
        record_dm_1(burn_f, hFinal, tn=n, f_ext=f_ext)


def makeNpulse_AFC(burnf, AFCparameters, recComb = False, shots, f_ext = '', pico_f_ext = ''):
    '''
    Uses make_AFC to create the AFC comb and then set the AWG and Picoscope to store and retrieve pulses from the AFC
    '''     
    make_AFC(burnf, AFCparameters, recComb = False, f_ext = '')   
    
    wf_24_cw(burn_f + 15e6 + 460.99e6, -26) #input into the IQ modulator
    #Set AWG to output storage pulse
    mc.setWvfmKey('Pulse')
    AWG_trig_out(1) 

    
    #Set picoscope to wait for ext trig
    t_s = 8*ns
    t_r = 100*us
    pico.setRapidBlock(ps, ch=['A','B'], Vrange = 0.2, nCaptures = shots, t_sample = t_s, 
                       t_record = t_r, trig = 'External', res = '15')    
    
    
    #AWG will trigger Pulse blaster
    #CH3 trigger picoscope.
    #CH5 suppress carrier EOM.
    #CH1 Open RF switch for AWG.
    #CH9 Bypass the AMP going to the EOM for low light level measurements
    pb.Sequence([
    (['ch5','ch9'], 0.5*us, LOOP, shots), #loop shots times
    (['ch5','ch9'], 0.5*us, WAIT),  #50us of 'silence' then have the pulse
    (['ch5','ch9'], 49.5*us),
    (['ch3','ch5','ch9'], 0.5*us),  #Record just before the pulse comes in 
    (['ch1','ch5','ch9'],t_r+10*us),#Leave enough time for the recording
    (['ch5','ch9'], 10*us, END_LOOP),
    (['ch5'],1*us)] ,loop=False,bStart=False)
        
    sleep(0.1)
    
    picoData = pico.getRapidBlock(ps)
    AWG_trig_out(0)
    
    return picoData
    
#==============================================================================
#     #Save formatted data.
#     file_name = time.strftime("C:\Users\Milos\Desktop\James\\" + "%Y-%m-%d Pico " + f_ext + '.mat')
# 
#     
#     sci.savemat(file_name, {'data': data_total})
#     plt.plot(t,data[0,:])
#     plt.show()
#==============================================================================
    
    

#

#
def wf_13_cw(wf_freq, wf_power):
    ''' Uses Windfreak1_3 to open wf and set to CW at a given freq and power on
    high power mode.'''
    if "wf_obj" not in locals():
        wf_obj = serial.Serial("COM5",115200,timeout = 1)  

    wf13.write_to_wf(wf_obj, wf_freq, 1, '0')
    wf13.write_power(wf_obj, wf_power)



def wf_24_cw(wf_freq, wf_power):
    ''' Similar to wf_13_cw, for the WF V2.4
    power is on 'high' setting'''    
    fname = "C:\\Users\\Milos\Desktop\\Er_Experiment_Interface_Code\\3.txt" #This is not important
    #Saves the settings for the WF at the 6th line of ^,a relic from old code.
    
    wf_instr = hb.windfreak(wf_freq, wf_power, 'high', filepath = fname, talk = 'YES', write = 1)
    return wf_instr
    
def wf_off(wf_instr):
    '''Turn off the WF 2.4'''  
    if "wf_instr" in locals():
        wf.Windfreak_ONOFF(0,'YES',wf_instr)
    
#

#
def SpecAnUnfreeze():
    ''' Triggers the Spectrum Analyser and sets it to continuous mode.'''
    pb.Sequence([(['ch4'], 2.5*ms) , (['ch2','ch5'], 2.5*ms)], loop=False)
    HP8560E_SpecAn_Trigger('FREE', 'CONTS', SpecAn)
    


def SpecAnSetUp(RefLev = -30):
    ''' Sets the spectrum analyser (HP 8560E) to have a sweep time of 50ms.
        Resolution Bandwidth of 30 kHz
        dB per div: 2
        Reference level to RefLev (default -30dB)
    '''
    SpecAn.write("RB 30000")
    SpecAn.write("ST 0.05")
    SpecAn.write('RL ' + str(RefLev))
    SpecAn.write('LG 2')
    HP8560E_SpecAn_RF(1, -10, SpecAn)
    
    sleep(0.5)
    
    a = SpecAn.query('RB?')
    b = SpecAn.query('ST?')
    c = SpecAn.query('RL?')
    d = SpecAn.query('LG?')
    
    print('Spectrum analyser set to:')
    print('Resolution Bandwidth {0}Sweep Time {1}Reference Level {2}'.format(a,b,c))
    print('dB per division {}'.format(d))
    
#

#
def AWG_trig_out(on = 1):
    ''' AWG will output a trigger if on = 1. Will not if on = 0'''
    mc.ads7.setTriggerOut(mode=on)
    if on:
        print('AWG output trigger is on.')
    else:
        print('AWG output tigger is off.')
#


#
if __name__ == "__main__":
    
    #REMEMBER TO CLOSE PS
    #pdb.set_trace()
    h_states = ['-5,2','-3,2','-1,2','1,2','3,2']


    if 'ps' not in globals():
        global ps
        ps = pico.open_pico()
    
    #Various parameters for the functions below
    burnf = 1.1e9
    AFCparam = [1,50] #BJT is in ms
    fext = ''
    shots = 5

#==============================================================================
#     # Run this just to spin pump
#     spin_pump_seq(spintime = 10*s,SpecAnSweep = 'Y',rec ='Y')
#     
#     # Run this just to spin jump
#     spin_jump(burnf,state = '3,2',rec = 'True', span = 20*MHz, teeth = 1, f_ext =fext,
#               bjt = 50, rec_offs = True)
# 
#     # Run this just to make a comb and image it
#     make_AFC(burnf, AFCparameters = AFCparam, recComb = True, f_ext = fext)
#     
#     # Run this to make a comb and send a pulse through it
#     makeNpulse_AFC(burnf, AFCparameters = AFCparam, recComb = False, shots=shot, 
#                    f_ext = fext, pico_f_ext = fext + ' pico')
#==============================================================================
    
    
    




     
        
        
        
        
        
    
    
    
    
    
    
    
    
    
    

