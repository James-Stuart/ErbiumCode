################################################################################
###									     ###
###		JAMES HOLE BURNING TESTING STUFF V1.0                        ###
###									     ###
################################################################################

from HP8560E_Spectrum_Analyser import *
import HP_Spectrum_Analyser as HP
import os
import time
import pylab
from time import sleep
import datetime
import binascii
import numpy as np
import matplotlib.pyplot as plt
import pulse_blaster as pb
import spectrum_image_HP8560E as SIH
import Stanford_FG as stan
import windfreakV2 as wf


#CH1 = Windfreak
#CH2 = SpecAn HP8560E
#CH3 = VCO
#CH5 LOW = burn (Laser power should be minimum)
#CH5 HIGH = scan(Laser power with no RF should be 2/3 max power)

#CH5 is used to switch between DC voltages to EOM, this is used to change the power
#of the carrier vs the sidebands. For scanning we want weak signal, so strong carrier with weak sidebands
#However we also require that the ratio between 1st and 2nd harmonics is as small as possible to limit
#noise due to Carrier - 2nd harmonic... ect
#The other setting allows for much higher power in the sidebands to give strong hole burning. 


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


def full_sweep(SpecAn):
    ''' Sets power to minimum and span to full spectrum '''
    SpecAn.write('CF' + str(1.45*GHz))
    SpecAn.write('SP' + str(2.9*GHz))



def record_trace1(SpecAn, filename = '', compensated = 'N', sweep_again = 'Y', n=1, burn_time = ''):
    ''' Writes a single trace from HP8560 SpecAn (taken via trigger) 
        to a data file "datestring + filename.txt"
        
        Compensated, 'Y'/'N', will subtract data from background reading SIH.run_offset.
        Sweep_again, 'Y'/'N', will return the SpecAn back to continous sweep mode.
     '''
##     
    #Date/Time information
    day = time.strftime("%d")
    month = time.strftime("%m")
    year = time.strftime("%Y")
    hour = time.strftime("%H")
    minute = time.strftime("%M")
    second = time.strftime("%S")
    
    date_string = year + '-' + month + '-' + day
    time_string = hour + ":" + minute + "." + second
    
    #Set up filename
##     filepath = "C:\Users\Milos\Desktop\James\\" + date_string + filename + str(minute)+','+str(second) +'.txt'
    filepath = "C:\Users\Milos\Desktop\James\\" + date_string + ' ' + filename +'.txt'
    try:
        os.remove(filename)
    except OSError:
        pass
    file = open(filepath,'w')
    
    #Write header
    file.write('Date: ' + date_string + '\n')
    file.write('Time: ' + time_string + '\n')
    SpecAn.write('CF?')
    center = float(SpecAn.read())
    print 'Center: ' + str(center)
    SpecAn.write('SP?')
    span = float(SpecAn.read())
    print 'Span: ' + str(span)
    file.write('Center freq: ' + str(center) + ' Span: ' + str(span) + '\n')
    SpecAn.write('RL?')
    ref_level = SpecAn.read()
    file.write('Reference Level: ' + ref_level + '\n')
    file.write('Data is offset subtracted: ' + compensated + '\n' + '\n')
    
    
    #Write 
    optional_header = 'Weird WF noise'
    file.write(optional_header + '\n')
    file.write('Burn time: ' + str(burn_time) + '\n')


    
    
    #From Milos's code HP8560E_Spectrum_Analyser, sets up SpecAn for a single sweep trace
    HP8560E_SpecAn_Trigger('EXT', 'SNGLS', SpecAn)
    #sets up registers to return interupt when sweep is complete
    SpecAn.write("CLEAR; RQS 4")    
    file.close()
    
    return filepath    
    



    
def record_trace2(SpecAn, filepath, filename = '', compensated = 'N', sweep_again = 'Y', n=1, burn_time = ''):
    #It will now trigger when signal is sent to the external trigger
    SpecAn.write('SP?')
    span = float(SpecAn.read())  
    SpecAn.write('CF?')
    center = float(SpecAn.read())    

##     SpecAn.write('TS')
##     #Waits for Spectrum Analyser to finish Data sweep
##     SpecAn.wait_for_srq(timeout = 30000)
    import time
    #time.sleep(10)
    

    file = open(filepath,'a')
    
        
    #Finds the off set save file (either full span or not)
    if span == 2900000000.0:
        save_file = "C:\\Users\\Milos\Desktop\\Er_Experiment_Interface_Code\\amplitude_offset_full.csv"
    else:
        save_file = "C:\\Users\\Milos\Desktop\\Er_Experiment_Interface_Code\\amplitude_offset.csv"   
    amplitude_offset = np.loadtxt(save_file,delimiter=",")
    
    #Waits for data, and converts into Hex
    x = np.linspace(center - span/2, center + span/2, 601)
    spec_data_temp = np.zeros(601)
  
    #Gets the trace from the SpecAn
    SpecAn.write('TRA?')
    binary = SpecAn.read_raw()
    spec_data_temp = np.frombuffer(binary, '>u2') # Data format is big-endian unsigned integers
##     hex_string = binascii.b2a_hex(binary)
##     spec_data_temp = np.zeros(601)
##     for j in range (601):            
##         spec_data_temp[j] = int('0x' + hex_string[j*4: j*4+4], 0)



    
    #Convert the data to dB based on SpecAn settings
    spec_data_db = SIH.convert2db(SpecAn,spec_data_temp)
    
    #Background subtracting
    if compensated == 'Y':
        compensated_data = np.subtract(spec_data_db,amplitude_offset)
    else:
        compensated_data = spec_data_db
    spec_data_db = compensated_data
    
    #Conjoins both x and spec_data_temp vectors and saves them to file     
    data = np.vstack([x, spec_data_db]).T
    np.savetxt(file, data, fmt='%.10e')
    sleep(0.01)
        
    file.close()
    pylab.ion()
    
    #Plots data
##     plt.plot(x,spec_data_db)
##     plt.pause(1)
    
    #Returns the SpecAn back to constant trigger
    if sweep_again == 'Y':
        HP8560E_SpecAn_Trigger("FREE", 'CONTS', SpecAn)
        
    return x, spec_data_db
    
    
    
    
    
    
def background(SpecAn, freq, span, res = 10*kHz, sweep = 1*s):
    ''' Run second
    Semi automates the background measurements on the HP8560E '''
    
    #First step laser off the absorption
    #Set SpecAn to be a desired freq, span...
    SpecAn.write('CF ' + freq)
    SpecAn.write('SP ' + span)
    SpecAn.write('RB ' + res)
    SpecAn.write('ST ' + sweep)
    
    #Run background measurement.
    SIH.save_offset(3)
    
    #Set span back to full so laser can be stepped back to absorption
    full_sweep(SpecAn)
    
    #Now Step laser back to absorption and Lock laser to right place
    
    
    
    
def run_offset(SpecAn, freq = 1.45*GHz, span = 2.9*GHz, res = 30*kHz, sweep = 50*ms, full_span = 'Y', show_window = 'Y'):
    ''' Sets desired SpecAn settings and runs Milos's background and free run
        programs.'''
    SpecAn.write("CF " + str(freq))
    SpecAn.write("SP " + str(span))
    SpecAn.write("RB " + str(res))
    SpecAn.write("ST " + str(sweep))
    
    sleep(0.5)
    SIH.save_offset(20, full_span)
        
    if show_window == 'Y':
        SIH.free_run_plot_window('Y', freq, span, full_span)
        
        
    

def holeburn(offset = 'N', args = [1.45*GHz, 2.9*GHz, 30*kHz, 1*s]):
    ''' No longer use this '''
    if offset != ('Y' or 'N'):
        raise error('argument must be "Y" or "N"')
        
    elif offset == 'Y':
        #Set SpecAn stuff
        SpecAn.write("CF " + str(args[0]))
        SpecAn.write("SP " + str(args[1]))
        SpecAn.write("RB " + str(args[2]))
        SpecAn.write("ST " + str(args[3]))
        sleep(0.5)
        SIH.save_offset(20)
        
    pb.hole_burn(3*s)
    SIH.free_run_plot_window('Y')
#    


 

def repump_sequence(SpecAn, SpecAn_Bool, start_freq, stop_freq, sweep_time = 200*ms):
    ''' After hole burning this will hopefully return atoms to 'normal' state. '''

    sweep_array = np.array([[start_freq, stop_freq, sweep_time]])
    [Stanford_FG, Stanford_Bool] = stan.Initialise_Stanford_FG()    
    
    #Tell me the Stanfords settings
    Stanford_FG.write('AMPL?')
    print 'Amplitude set to ' + Stanford_FG.read()    
    Stanford_FG.write('OFFS?')
    print 'Offset set to ' + Stanford_FG.read()    
    
    #set up and upload sweep array to stanford
    [num_array, waveform_length] = stan.VCO_Sweep(sweep_array, Stanford_FG, Stanford_Bool, 'op amp', SpecAn, SpecAn_Bool)
    stan.Upload_to_Stanford_FG(num_array,waveform_length, Stanford_FG)
    
    #Set pulseblaster to run VCO via ch3
    pb.repump()




def spin_polarise(SpecAn, SpecAn_Bool, start_freq, direction = 'backwards', pumps = 10):
    ''' Controls stanford plugged into VCO to spin pump ensomble by scanning over
    delta m = +/-1. 
    MIN FREQ: 875MHz'''
    sweep_array = np.array([[start_freq, start_freq + 700*MHz, 100*ms]])
    print np.max(sweep_array)/1e6
    [Stanford_FG, Stanford_Bool] = stan.Initialise_Stanford_FG()
    
    #Tell me the Stanfords settings
    Stanford_FG.write('AMPL?')
    print 'Amplitude set to ' + Stanford_FG.read()    
    Stanford_FG.write('OFFS?')
    print 'Offset set to ' + Stanford_FG.read() 
    
    if direction == 'backwards':
        [num_array, waveform_length] = stan.VCO_Sweep_backwards(sweep_array, Stanford_FG, Stanford_Bool, 'op amp 3.7', SpecAn, SpecAn_Bool)
    elif direction == 'forwards':
        [num_array, waveform_length] = stan.VCO_Sweep(sweep_array, Stanford_FG, Stanford_Bool, 'op amp 3.7', SpecAn, SpecAn_Bool)
    else:
        raise error('direction must be either backwards or forwards')
        
    stan.Upload_to_Stanford_FG(num_array,waveform_length, Stanford_FG)
    
    #Sets pulseblaster to run VCO via ch3
    time = pumps*100*ms
    pb.spin_pump(time)
    pb.Sequence([(['ch3'], 10)] + [(['ch3'], 10)] + [(['ch3'], 10)] + [(['ch3'], 10)] + [(['ch3'], 10)] + [(['ch3'], 10)] + [(['ch3'], 10)] + [(['ch3'], 10)] + [(['ch2','ch5'], 1*s)
    ],loop=False)   
    



def windfreak(freq, dB, power_state, filepath, talk = 'YES', write = 0):
    ''' Basic Windfreak V2 control, sets frequency, and power (controling whether
        it's in high or low power mode too). And writes WF power settings into file.
        freq: 0 - 4.4GHz in Hz
        dB: -31 - 0
        power_state: 'high','low'
    '''
    if freq <= 4.4e9 and 0 <= freq:
        pass
    else:
        raise('error: freq must be within 0 - 4.4GHz')
    if dB <= 0 and -31.5 <= freq:
        pass
    else:
        raise('error: dB must be within 0 - -31.5')
    if power_state in ['high','low']:
        power_state_binary = 1 if power_state == 'high' else 0
    else:
        raise('error: power state must be "high" or "low"')            
    
    instr,bSuccess = wf.Initialise_Windfreak()
    wf_freq = wf.Windfreak_freq(freq, talk, instr) #Sets WF freq and records the set freq  
    
    dB_63 = 2*dB + 63 
    wf_power_63 = wf.Windfreak_power_level(dB_63, talk, instr)
    wf_power = (wf_power_63 - 63)/2
    
    wf_power_state_binary = wf.Windfreak_HILO(power_state_binary, talk, instr)
    wf_power_state = ' high' if wf_power_state_binary == 1 else ' low' 
    
    if write == 1:
        #open hole burning data file and replace line 7 with WF settings
        file = open(filepath,'r+')
        data = file.readlines()
        file.seek(0)
        data[6] = 'WF power: ' + str(wf_power)  + str(wf_power_state) 
        file.writelines(data)
        file.close()
    



    
if __name__ == "__main__":
    
    def full_offset():
        run_offset(SpecAn, full_span = 'Y')
        full_sweep(SpecAn)
        SIH.free_run_plot_window('Y',full_span = 'Y')
##     run_offset(SpecAn, freq = 1.8*GHz, span = 100*MHz, res = 30*kHz, sweep = 50*ms, full_span = 'N', show_window = 'N')
##     SIH.free_run_plot_window('Y', full_span = 'N')


    def burn_sequence(burn, burn_freq, power):
##         burn = 0.1*s
##         burn_freq = 2.525*GHz
        #Hole burning sequence
        run_offset(SpecAn, freq = 1.595*GHz, span = 10*MHz, res = 100*kHz, sweep = 250*ms, full_span = 'N', show_window = 'N')
        filepath = record_trace1(SpecAn, compensated = 'Y', n=1, burn_time = burn)
        windfreak(burn_freq, power, 'high', filepath, write = 1)
        pb.hole_burn(burn)
        x,y=record_trace2(SpecAn, filepath, compensated = 'Y', n=1, burn_time = burn)
        
        sleep(0.5*s)

##         #Rempump will only go as low as 875 MHz
##         repump_sequence(SpecAn, SpecAn_Bool, 1.4*GHz, 2.4*GHz)
##         sleep(0.5)
##         #Full 2.9GHz scan
        full_sweep(SpecAn)
        SIH.free_run_plot_window('Y',full_span = 'Y')
        return x,y

    def burn_n_sit(burn, freq1):
##         burn = 0.02*s
##         freq1 = 2.560*GHz
        #Hole burning sequence
        run_offset(SpecAn, freq = freq1, span = 1*MHz, res = 30*kHz, sweep = 50*ms, full_span = 'N', show_window = 'N')
        pb.hole_burn(burn)
        record_trace(SpecAn, compensated = 'Y', n=1, burn_time = burn)
        sleep(0.5*s)

        SpecAn.write('CF ' + str(freq1))
        SpecAn.write('SP 5000000')
        SIH.free_run_plot_window('N',full_span = 'N')    
  


    def spin_pump_seq(freq,j):
        spin_polarise(SpecAn, SpecAn_Bool, freq, direction = 'forwards', pumps = 20)
        SIH.free_run_plot_window('Y',full_span = 'Y')
        

##     run_offset(SpecAn)
##     SIH.free_run_plot_window('Y',full_span = 'Y')

##     times = np.array([0.02,0.01,0.009,0.008,0.007,0.006,0.005,0.004,0.003,0.002,0.001])
##     powers= np
##     frequency = 2.31*GHz
##     for loopy in range(len(times)):
##         var1 = times[loopy]
##         var2 = powers
##         burn_sequence(var1, frequency, var2)
##         frequency += 5*MHz
##         sleep(1)
## 
## full_sweep(SpecAn)
##     spin_pump_seq(2.4*GHz,1)
## x,y=burn_sequence(0.25,2.541*GHz,-25)    

## HP8560E_SpecAn_Trigger("FREE", 'CONTS', SpecAn)
##     burn_n_sit()

## # AM PM EOM MODULATOR THINGSS
##     filepath = record_trace1(SpecAn, compensated = 'Y', n=1, burn_time = 0)
##     pb.Sequence([(['ch5'], 0.5*s)] + [(['ch2','ch5','ch4'], 100*ms)] + [(['ch2','ch5'], 100*ms)], loop=False)
##     x,y=record_trace2(SpecAn, filepath, compensated = 'Y', n=1, burn_time = 0)


## SpecAn.write('FA 2899000000')
## SpecAn.write('FB 2901000000')

SpecAn.write('MKPK HI')
num = SpecAn.query('MKA?')
## print num


    



