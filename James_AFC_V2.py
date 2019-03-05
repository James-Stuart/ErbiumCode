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
    if state == '5,2':
        print("Use function spin_jump_dmneg1 instead")
        raise RuntimeError("I'm afraid I cannot do that Dave, burning on the Delta m = -2 means the highst hyperfine I can get to is |3/2>.")
        
    if state not in state_dict: #Check if variable state is valid
        print('Error, variable state must be in [3,2 ... -7,2]')
        
    print("Initial burn on the Delta m = -2")
    target_state = state_dict[state]
    
    #I am keeping the -107.64 to allow the ability to image the 5/2> easily
    #DELTA M=-2 |7/2> location is -903.02MHz
    e_gap = np.array([-107.60, -218.09, -323.2, -415.50, -488.20, -535.89, 460.99])*MHz #Gaps in hyperfine energy levels
##     e_gap = np.array([0, -107.60, -218.09, -323.2, -415.50, -488.20, -535.89, 460.99])*MHz #Gaps in hyperfine energy levels
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
    
def spin_jump_dmneg1(freq,state = '5,2',rec = 'True', span = 20*MHz):
    ''' Sets the 8GB AWG to a given frequency and burns a 100kHz hole, gives the option to 
        record the anti-hole created.
        Then burns on top of the anti-hole with a larger chirp 500 kHz - 2 MHz 
        '''
    #Splittings are [107.64, 110.42,105.17,92.34,73.02,47.94]
    #delta m = -1 energy gaps 7/2 -> -7/2: [0, -107.64, -218.06, -323.23, -415.57, -488.59, -536.53]+some offset
    state_dict = {'5,2': 0,'3,2': 1,'1,2': 2,'-1,2': 3,'-3,2': 4,'-5,2': 5,'-7,2': 6}
    if state not in state_dict: #Check if variable state is valid
        print('Error, variable state must be in [5/2, 3/2... -7/2]')
        
    print("Initial burn on the Delta m = -1")
    target_state = state_dict[state]

    e_gap = np.array([-107.64, -218.06, -323.23, -415.57, -488.59, -536.53, 460.32])*MHz #Gaps in hyperfine energy levels
    #From 7/2 - 5/2 -> -3/2 - -5/2
    str_name = [' spin jumped 5,2 antihole',' spin jumped 3,2 antihole',' spin jumped 1,2 antihole',' spin jumped -1,2 antihole',
    ' spin jumped -3,2 antihole',' spin jumped -5,2 antihole',' spin jumped -7,2 antihole']
    
    #Perform the first burn (which should have a narrower chiep and quicker burn time
    if target_state >= 0:
        mc.setWvfm(0,teeth-1)
        burn_sequence_AWG(burn = 200*ms, burn_freq= freq, record = rec, rec_freq = freq - 107.64*MHz, rec_span = span, f_name = ' spin jumped 5,2 antihole via dm1')# ' + str(i))
    
    #Perform the rest of the spin jump down to the desired level.
    #Cant look at the anti-hole in each level though
    j = target_state
    print(target_state)
    if target_state > 0:
##         mc.setWvfm(teeth,teeth*(j+1)-1)#No  Comb clean up. 
        mc.setWvfm(teeth,teeth*(j+2))  #For Comb clean up.
        burn_sequence_AWG(burn = 500*ms*(j), burn_freq= freq+e_gap[j-1], record = rec, rec_freq = freq+e_gap[j], rec_span = span, f_name = str_name[j] + ' via dm1')
#

#
def spin_jump_time_measurement(freq, times, state = '5,2'):
    ''' OLDER SLOWER VERSION, USE ONLY IF NEW ONE BROKE
        Preforms spin jump to a certain hyperfine and then records the anti-hole a give time
        after the hole was originally burnt '''
    HP8560E_SpecAn_Trigger('EXT', 'SNGLS', SpecAn)
    sp = 10*MHz
    
    state_dict = {'5,2': 0,'3,2': 1,'1,2': 2,'-1,2': 3,'-3,2': 4,'-5,2': 5}
    if state not in state_dict: #Check if variable state is valid
        print('Error, variable state must be in [5/2, 3/2... -5/2]')
    
    p = state_dict[state]
    e_gap = np.array([-107.64, -217.98, -323.19, -415.47, -488.22, -536.46])*MHz #Gaps in hyperfine energy levels
    
    #Record background measurements
    HP8560E_SpecAn_Trigger("FREE", 'CONTS', SpecAn)
    pb.Sequence([(['ch2','ch5'], 1*ms)], loop=False)
    hb.run_offset(SpecAn, freq = freq+e_gap[p], span = sp, res = 30*kHz, sweep = 50*ms, full_span = 'N', show_window = 'N',n = 5)
    
    #Spin Jump
    HP8560E_SpecAn_Trigger('EXT', 'SNGLS', SpecAn)
    spin_jump(freq,state,rec = 'False',span = sp)
    

    
    #Stop SpecAn sweeping over anti hole, burn final anti-hole and then suppresses carrier
    #Take spectra at time '0'
    HP8560E_SpecAn_Trigger("FREE", 'CONTS', SpecAn) #Record
    SpecAn.write("CF " + str(freq + e_gap[p]))
    SpecAn.write("SP " + str(sp))
    filepath = hb.create_file(SpecAn, compensated = 'Y', n=1, burn_time = 0, filename = ' '+ state +' zero ' + str(time[i]) + 's')
    pb.Sequence([   (['ch5'], 1*s),
                    (['ch2','ch4','ch5'], 70*ms), #RF Switch, Trigger SpecAn, EOM Bias on 
                    ([ ], 100*ms),              #turn off ch2,ch5, suppress carrier/RF
                    ], loop=False)  
    hb.record_trace(SpecAn, filepath, compensated = 'Y', sweep_again = 'Y', n=1, burn_time = '')
    HP8560E_SpecAn_Trigger('EXT', 'SNGLS', SpecAn)    
    
        
    sleep(times[i]) #wait
    HP8560E_SpecAn_Trigger("FREE", 'CONTS', SpecAn) #Record
    filepath = hb.create_file(SpecAn, compensated = 'Y', n=1, burn_time = 0, filename = ' '+ state +' ' + str(time[i]) + 's')
    pb.Sequence([   (['ch5'], 1*s),
                    (['ch2','ch4','ch5'], 70*ms), #RF Switch, Trigger SpecAn, EOM Bias on 
                    (['ch2','ch5'], 100*ms),
                    ], loop=False)  
    hb.record_trace(SpecAn, filepath, compensated = 'Y', sweep_again = 'Y', n=1, burn_time = '')
    HP8560E_SpecAn_Trigger('EXT', 'SNGLS', SpecAn)    
        
def spin_jump_time_measurement_faster(times, burn_f, state = '5,2'):
    ''' Spin polarizes and spin jumps the ensemble to a given [state].
        Then it records the anti-hole after a certain amount of time given by [times]
        This one is faster because it spin polarizes every n recordings rather than
        every recording.'''
    freq = burn_f
    count = 4
    sp = 20*MHz
##     sp = 2.9*GHz
    
    state_dict = {'5,2': 0,'3,2': 1,'1,2': 2,'-1,2': 3,'-3,2': 4,'-5,2': 5,'-7,2': 6}
    if state not in state_dict: #Check if variable state is valid
        print('Error, variable state must be in [5,2, 3,2... -5,2]')
    
    p = state_dict[state]
    e_gap = np.array([-107.60, -218.09, -323.2, -415.50, -488.20, -535.89, 1453.5])*MHz #Gaps in hyperfine energy levels
    
    pl.ioff()    
    for i in range(len(times)):
        count += 1

    
        if count == 5:
            count = 0
            
            HP8560E_SpecAn_Trigger("FREE", 'CONTS', SpecAn)
            
            SpecAn.write('CF ' + str(1.45*GHz))
            SpecAn.write('SP ' + str(2.9*GHz))
            spin_pump_seq(spintime = 10*s, SpecAnSweep = 'Y', rec = 'N')
        
            #Record background measurements
            HP8560E_SpecAn_Trigger("FREE", 'CONTS', SpecAn)
            pb.Sequence([(['ch2','ch5'], 1*ms)], loop=False)
            hb.run_offset(SpecAn, freq = freq+e_gap[p], span = sp, res = 30*kHz, sweep = 50*ms, full_span = 'N', show_window = 'N',n = 5)
##             hb.run_offset(SpecAn, freq = 1.45*GHz, span = 2.9*GHz, res = 30*kHz, sweep = 50*ms, full_span = 'N', show_window = 'N',n = 5)


            #Stop SpecAn sweeping over anti hole, burn final anti-hole and then suppresses carrier
            HP8560E_SpecAn_Trigger('EXT', 'SNGLS', SpecAn)
        
        
            #Spin Jump
            spin_jump(freq,state,rec = 'False',span = sp, teeth = 1)
            
                    
            #Take spectra at time '0'
            SpecAn.write("CF " + str(freq+e_gap[p]))
            SpecAn.write("SP " + str(sp))
##             SpecAn.write("CF " + str(1.45*GHz))
##             SpecAn.write("SP " + str(2.9*GHz))
            f_name = ' ' + state + ' zero ' + str(times[i]) + 's'
            filepath = hb.create_file(SpecAn, compensated = 'Y', filename = f_name)
            pb.Sequence([   (['ch5'], 1*s),
                            (['ch2','ch4','ch5'], 70*ms), #RF Switch, Trigger SpecAn, EOM Bias on 
                            ([ ], 100*ms),              #turn off ch2,ch5, suppress carrier/RF
                            ], loop=False)  
            hb.record_trace(SpecAn, filepath, compensated = 'Y', sweep_again = 'N', n=1, burn_time = '')
            HP8560E_SpecAn_Trigger('EXT', 'SNGLS', SpecAn)    
            
            print('Waiting ' + str(times[i]) + ' seconds.')
            sleep(times[i]) #wait

            
        else:
            t = times[i] - times[i-1]
            print('Waiting ' + str(t) + ' seconds.')
            sleep(t)
            
        #Record
        f_name = ' ' + state + ' ' + str(times[i]) + 's'
        filepath = hb.create_file(SpecAn, compensated = 'Y', filename = f_name)
        pb.Sequence([   (['ch5'], 1*s),
                        (['ch2','ch4','ch5'], 70*ms), #RF Switch, Trigger SpecAn, EOM Bias on 
                        ([ ], 100*ms),
                        ], loop=False)  
        fName = hb.record_trace(SpecAn, filepath, compensated = 'Y', sweep_again = 'N', n=1, burn_time = '') 
        dat=np.loadtxt(fName, skiprows=10)
        pl.plot(*dat.T)
        #pl.draw()
        plt.pause(0.1)  
        
    pl.show()
    sleep(1)        
        
    HP8560E_SpecAn_Trigger("FREE", 'CONTS', SpecAn)    
        
        

def all_time_measurements(t_array, burn_f, state_array):
    
    for hyperfine in state_array:
        for time in t_array:
            t = [time]
            spin_jump_time_measurement_faster(t, burn_f, hyperfine)
#

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
WAIT = 8 #From the Pulseblaster code. for telling Pb to wait for trigger
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


def run_AFC(burnf, AFCparameters, recComb = False, f_ext = '', pico_f_ext = ''):
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
    for i in range(shots):
    #1ms allows for a time gap between each shot
        pb.Sequence([(['ch5'], 0.5*us), 
        (['ch5'], 0.5*us, WAIT),  #50us of 'silence' then have the pulse
        (['ch5'], 49.5*us),
        (['ch3','ch5'], 0.5*us),  #Record just before the pulse comes in 
        (['ch1','ch5'],t_r+10*us),#Leave enough time for the recording
        (['ch5'], 10*us)] ,loop=False,bStart=False)
        
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
def comb_background_abs(burn_f = 1.1*GHz,shots = 1000, delay = 0):
    ''' Idea: Spin pump crystal 
              Burn a narrow hole where the AFC will be (100 kHz)
              Send broad pulse through quickly after (>1ms after, MHz broad)
    What comes out should give a measurement of the background where the AFC will be
    before spin jumping.
    
    Turn WF on
    Set up PS for RAPID BLOCK mode'''  
    
    mc.setWvfm(0)
    sleep(0.1)
    pb.Sequence([(['ch1','ch5'], 50*ms) , (['ch5'], 1*ms)], loop=False)
    sleep(0.1)
    
    
    AWG_trig_out()
##     wf = wf_24_cw(burn_f + 19e6 + 460.99e6, -10)
    mc.setWvfm(1)
    sleep(0.1)
    
    arr = [(['ch5','ch6'], 10*s), (['ch5'], 20*ms)] #10s to spin pol. crystal, 20ms to let the mems switch switch.  
    pb.Sequence(arr,loop=False)
    time.sleep(10.1)
    
    pb.ProbBurnLoop(shots = 1000)
    time.sleep(shots*7e-4) #replace this is Wvfm time length
    
    mc.setWvfm(2)
    pb.ProbBurnLoop(shots = 1000)
    time.sleep(shots*5e-4) #replace this is Wvfm time length

##     AWG_trig_out(0) #Tends to turn trig off too soon
##     wf_off(wf)
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
    ''' Similar to wf_13_cw, for the WF V2.4'''    
    fname = "C:\\Users\\Milos\Desktop\\Er_Experiment_Interface_Code\\3.txt" #This is not important
    #Saves the settings for the WF at the 6th line of ^,a relic from old code.
    
    wf_instr = hb.windfreak(wf_freq, wf_power, 'high', filepath = fname, talk = 'YES', write = 1)
    return wf_instr
    
def wf_off(wf_instr):
    
    
    if "wf_instr" in locals():
        wf.Windfreak_ONOFF(0,'YES',wf_instr)
    
#

#
def SpecAnUnfreeze():
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
def spin_jump_record_repeat(burn_f, h_state, file_name, teeth = 1, n = 1):
    ''' Spin poliarises the crystal once. Then repeatedly spin jump's and records the anti-hole.'''
    HP8560E_SpecAn_Trigger('FREE', 'CONTS', SpecAn)  
    spin_pump_seq(spintime = 10*s, SpecAnSweep = 'N', rec = 'N')
    rec_span = 20*MHz
    
##     state_dict = {'3,2': 0,'1,2': 1,'-1,2': 2,'-3,2': 3,'-5,2': 4,'-7,2': 5}
##     num = state_dict[h_state]
##     bjt_ext = 5/num
    
    #Initial spin jump (longer Burn Jump Time)
    num_len = int(np.ceil(np.log10(n)))
    zero = '0'
    zeros = zero*num_len
    spin_jump(burn_f,state = h_state ,rec = 'True', span = rec_span, teeth = teeth, f_ext = file_name + ' ' + zeros, bjt = 50)#*bjt_ext) 
    for i in range(n-1):
        #Each subsequent spin jump should need a much shorter Burn Jump Time
        spin_jump(burn_f,state = h_state ,rec = 'False', span = rec_span, teeth = teeth, f_ext = file_name + ' ' + str(i+1).zfill(num_len), bjt = 50, rec_offs = False)
        
    

    #Records the 2.9GHz span after all measurements
    filepath = hb.create_file(SpecAn, compensated = 'Y', n=1, burn_time = 0, filename = ' Spin pumped after spinjump ' + h_state)
    sleep(100*ms)
    pb.Sequence([   (['ch5'], 0.5*s),
                    (['ch2','ch4','ch5'], 50*ms), #RF Switch, Trigger SpecAn, EOM Bias on 
                    (['ch2','ch5'], 100*ms),
                    ], loop=False)
    hb.record_trace(SpecAn, filepath, filename = ' Spin pumped after spinjump ' + h_state, compensated = 'Y', sweep_again ='N', n=1, burn_time = '')

    
aVariable1 =1   

loc = None
glob = None


if __name__ == "__main__":
    
    #REMEMBER TO CLOSE PS
    #pdb.set_trace()
##     h_states = ['-5,2','-3,2','-1,2','1,2','3,2']
##     for state in h_states:
##     spin_jump_record_repeat(n= 1,burn_f = 1.04*GHz, h_state = '-7,2', file_name = 'test')
##     freqs = [194.9435, 194.9436, 194.9437, 194.9438, 194.9439, 195.1618, 195.1619, 195.162, 195.1621, 195.1622]
##     for freq in freqs:
    t_list = [0.1,0.2,0.3,0.5,0.7,1,1.5,2,3,4,5,7,9]
##     for t in t_list:
##         print('\n')
##         print('Time: ' + str(t)+'\n')
##         print('\n')
##             #SpinpumpSite2BurnSite1(f_name = 'Spinpump, burn at ' + str(freq) + 'THz ' + str(i), freq = freq)
##         f_str = 'Spinpump, burn spatially seperated for ' + str(t) + ' s, delay 20s'
##         spinpump_delay(f_name = f_str, delay = 20, secondLpath = True, latchT = t)
##         
##     for i in range(5):
##         print('\n')
##         print('Loop: ' + str(i))
##         print('\n')
##         spinpump_delay(f_name = 'Spinpump, delay 20s' + str(i), delay = 20, secondLpath = False)
        
    freq = 194.9404
    for t in t_list:
        print('\n')
        print('Time: ' + str(t)+'\n')
        print('\n')        
        SpinpumpSite2BurnSite1(f_name = 'Spinpump, burn at ' + str(freq) + 'THz for' + str(t) + 's', freq = freq)
    
##     if 'ps' not in globals():
##         global ps
##         ps = pico.open_pico()

##     for i in range(5):
##         burn_f = 1.1*GHz
##         h_state = '-7,2'
##         file_suff = 'rec dm1 -0.99s delay' + str(i) #filename for direct comb imaging
##         teeth = 1
##         loc = locals()
##         glob = globals()
    ##     wf_24_cw(burn_f + 20e6 + 460.99e6, -10)#Freq offset from the pulses freq.
##         f_ext = 'improved' #File name for ps recordings
##         voltRange = 0.2

##         HP8560E_SpecAn_Trigger('FREE', 'CONTS', SpecAn)     
##         spin_pump_seq(spintime = 10*s, SpecAnSweep = 'N', rec = 'N')
    ##     reference_pulse(f_ext, voltRange)

##         save_offset_custom(SpecAn, 5, "1.txt",freq = burn_f + 1557*MHz, span = 270*MHz)
    ##     save_offset_custom(SpecAn, 5, "2.txt",freq = burn_f + 1472*MHz, span = 20*MHz)
    ##     save_offset_custom(SpecAn, 5, "3.txt",freq = burn_f + 1529*MHz, span = 20*MHz)
##         spin_jump(burn_f,state = h_state ,rec = 'True', span = 270*MHz, teeth = teeth, f_ext = file_suff, bjt = 500) 
        
        
##         record_dm_1(burn_f, file_suff + ' ' + h_state, tn = teeth)
    
    ##########################################################################
##     shots=10
##     
##     ########################################################################## 
##     #Set AWG to output storage pulse
##     mc.setWvfmKey('Pulse')
##     AWG_trig_out(1)    
##     
##     #Set picoscope up to collect data and wait for external trigger
##     t_s = 4*ns
##     r_l = 20*us
##     t_sample,res = pico.run_rapid_block(ps, Vrange = voltRange, n_captures = shots, t_sample = t_s, record_length = r_l)
##     n_data = r_l/t_s
##     sleep(0.1)
##     
##     #CH3 trigger picoscope.
##     #CH5 suppress carrier EOM.
##     #CH1 Open RF switch for AWG.
##     for i in range(shots):
##     #1ms allows for a time gap between each shot
##         pb.Sequence([(['ch5'], 0.5*us), 
##         (['ch5'], 0.5*us, WAIT), 
##         (['ch5'], 49.5*us),
##         (['ch3','ch5'], 0.5*us), 
##         (['ch1','ch5'],50*us), 
##         (['ch5'], 1*ms)] ,loop=False,bStart=False)
##         
##     sleep(0.1)
##     
##     #Get data from picoscope
##     data = pico.get_data_from_rapid_block(ps)
##     t = np.arange(data.shape[1])*t_s
##     data_total = np.vstack([t,data])
##     data_total = data_total.T
##     
##     AWG_trig_out(0)
##     #Save formatted data.
##     file_name = time.strftime("C:\Users\Milos\Desktop\James\\" + "%Y-%m-%d Pico " + f_ext + '.mat')

##     
##     sci.savemat(file_name, {'Vrange': voltRange,'sampleRate': t_s,'data': data_total})
##     plt.plot(t*1e6,data[0,:])
##     plt.xlabel('us')
##     plt.show()




        
    ##     pulse_test()

    ##     make_AFC(n = teeth, bjt = 500, burn_f = burn_f, hyperfine = h_state, f_ext = 'AFC echo',
    ##     bandwidth = 4.5*MHz, record = "False", shots = 1)
        
    ##     wf_13_cw(137.5,-10)
##     wf_24_cw(burn_f + 10e6 + 460.99e6, -10)
##     reference_pulse(f_ext='ref test')
##     make_AFC(n=teeth, bjt=500, burn_f=burn_f, hyperfine=h_state, f_ext = 'wide,300kHz,spacing,1.2MHz', record = "True", shots = 10)
        
        
        
        
        
        
        
        
    
    
    
    
    
    
    
    
    
    
    
    
    
##     SpecAn.write('CF ' + str(1.45*GHz))
##     SpecAn.write('SP ' + str(2.90*GHz))
    

    
    
##     burn_f = 1.15*GHz
##     hyperfine = ['-7,2']
##     hyperfine = ['1,2']
##     for k in range(len(hyperfine)):
##     for k in range(1):
    
    ##     hyperfine = '3,2'
##     spin_pump_seq(spintime = 10*s, SpecAnSweep = 'Y', rec = 'Y')
##     SIH.free_run_plot_window('Y', full_span = 'Y')

        #Record some on the Delta m = 1, Spinpump first
##         save_offset_custom(SpecAn, 5, "1.txt",freq = burn_f + 1443*MHz, span = 40*MHz, res = 30*kHz, sweep = 50*ms)
##         save_offset_custom(SpecAn, 5, "2.txt",freq = burn_f + 1472*MHz, span = 20*MHz, res = 30*kHz, sweep = 50*ms)
##         save_offset_custom(SpecAn, 5, "3.txt",freq = burn_f + 1529*MHz, span = 20*MHz, res = 30*kHz, sweep = 50*ms)

##         spin_jump(burn_f,state = hyperfine[k],rec = 'True', span = 10*MHz, teeth = n)  
##         record_dm_1(burn_f, hyperfine[k])
##         SpecAn.write('SRCPWR -10')
    
    
##     hb.full_sweep(SpecAn)
##     sleep(0.1)
##     SIH.free_run_plot_window('Y', full_span = 'Y')

    #To change SpecAn Power, values between -10 and 2. -10 being default
##     SpecAn.write('SRCPWR -10')


        
