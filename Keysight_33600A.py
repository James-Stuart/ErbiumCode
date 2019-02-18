#=============================================================
# KEYSIGHT 33600A Series Waveform generator  ||  James 2017
#	Initialiser and basic operations code.
#=============================================================

import sys
from ctypes import *
from time import clock
from time import sleep
from visa import *
from struct import *
import numpy as np
import os
import sys
rm = ResourceManager()

Hz = 1
kHz = 10**3
MHz = 10**6
GHz = 10**9


us=10**-6;
ns=10**-9;
ms=10**-3;
s=1;

def initialise():
    ''' Initialises the Keysight waveform generator from a USB address, 
        allowing commands to be entered via the handle "keysight".
    '''
    keysight = rm.open_resource('USB0::0x0957::0x5707::MY53801566::INSTR')
    print 'Hello my name is:'
    keysight.write('*IDN?')
    thing = keysight.read()
    print thing
    return keysight
    
    
def wave(keysight, freq, amp, offset = 0, channel = 1, function = 'SIN'):
    ''' Makes a waveform from the default functions.
        sine,square,triangle,ramp,noise,arbitrary,DC with the commands
        SIN,SQU,TRI,RAMP,PULS,PRBS,NOIS,ARB,DC
    '''
    waveforms = ['SIN','SQU','TRI','RAMP','PULS','PRBS','NOIS','ARB','DC']
    if function not in waveforms:
        raise ValueError('error: unknown waveform fuction')
    
    com_str = 'SOUR' + str(channel) + ':APPL:' + function + ' ' + str(freq) \
    + ',' + str(amp) + ',' + str(offset) 
    
    keysight.write(com_str)
    
    
def channel_off(keysight,channel):
    com_str = 'OUTP'+str(channel)+' OFF'
    keysight.write(com_str)
    
    
def arb(keysight, sample_rate = 20*kHz, amp_list = [], channel = '1', arb_file = ''):
    ''' DOESNT WORK RIGHT NOW
    
        Takes in an input of sample rate, list of amplitudes and an optional 
        channel argument. Writes an arbitrary waveform to the keysight via a 
        .arb file.
    '''
    if arb_file == '':
        v_high = np.round(max(amp_list),2)
        v_low = np.round(min(amp_list),2)
        length = len(amp_list)
        
        off_set = (v_high + v_low)/2
        v_range = v_high - off_set
        
        data = amp_list - off_set #centers data set about 0
        data = data/v_range*2**15 #sets max/min of data set to be 2^15,-2^15
        data = data.astype(int)   #makes sure data set composed of integers
        
        #Replaces file if need be
        filename = 'C:\Users\Milos\Desktop\James\\33600A_arb_wave.arb'
        try:
            os.remove(filename)
        except OSError:
            pass
        
        #Create .arb waveform file
        file = open(filename,'w')
        file.write('File Format:1.10 \nChecksum:0 \n')
        file.write('Sample Rate:' + str(sample_rate) + '\n')
        file.write('High Level:' + str(v_high) + '\n')
        file.write('Low Level:' + str(v_low) + '\n')
        file.write('Marker Point:50 \n')
        file.write('Data Type:"short" \n')
        file.write('Filter:"off" \n')
        file.write('Data Points:' + str(length) + '\n')
        file.write('Data: \n')
        for i in range(len(data)):
            file.write(str(data[i]) + '\n')
            
        file.close()
        
        com_str = 'SOUR' + str(channel) + ':FUNC:ARB'
        keysight.write(com_str)
        keysight.write('FUNC:ARB "C:\Users\Milos\Desktop\James\\33600A_arb_wave.arb"')
        
        #ketsight.write('MMEM:LOAD:DATA "C:\Users\Milos\Desktop\James\\33600A_arb_wave.arb"')
        #keysight.write('FUNC:ARB "C:\Users\Milos\Desktop\James\\33600A_arb_wave.arb"')
        #keysight.write('FUNC ARB')
    
    #If a file for the arb wavefunction already exists, skip the previous
    else:
        com_str = 'FUNC:ARB "' + str(arb_file) + '"'
        keysight.write(com_str)
    
def abort(keysight):
    ''' Halts all sequences to keysight and returns it to an idle state.
    '''
    keysight.write('ABOR')
    
    
    
def sweep(keysight, start, stop, sweep_time, amp = 1, channel = 1, function = 'SIN', offset = 0):
    '''Takes initial parameters and uses keysights sweep function to... make a sweep
    '''
    waveforms = ['SIN','SQU','TRI','RAMP','PULS','PRBS','NOIS','ARB','DC']
    if function not in waveforms:
        raise ValueError('error: unknown waveform fuction')
        
    com_str = 'SOUR' + str(channel) + ':APPL:' + function + ' ' + str(start) \
    + ',' + str(amp) + ',' + str(offset) 
    com_str2 = 'SOUR' + str(channel)
    
    keysight.write(com_str)
    keysight.write(com_str2 + 'FREQ:MODE SWE')
    keysight.write(com_str2 + 'FREQ:START ' + str(start))
    keysight.write(com_str2 + 'FREQ:STOP ' + str(stop))
    keysight.write(com_str2 + 'SWE:TIME ' + str(sweep_time))
    keysight.write('OUTP' + str(channel) + ' 1')
    
    
def off(keysight):
    '''Temp function that turns off outputs
    '''
    keysight.write('OUTP off')
    


def array_to_binary_block(data, scl=True):
    ''' Totally stole from Morgan.
        Converts array "data" into binary.
    '''
    data=np.array(data, dtype='f8')
    if scl:
        data/=abs(data).max()
        data*=(2**15-1)
        
    data=np.rint(data).astype('i2')
    dataBytes=data.tobytes()
    N=len(dataBytes)
    Nstr=str(N)
    return ( "#{0}{1}".format(len(Nstr), Nstr),  dataBytes )
    
    
def uploadWaveform(keysight, data, scl=True, name="VOLATILE", chanNum=0, bCareful=True, bSetAsOutput=True):
    ''' Also stolen from Morgan, uploads Arb waveform arrays to the keysight.
    '''
    #Convert data array into binary.
    binBlockHead, binBlockValues=array_to_binary_block(data,scl=scl)
    
    #Clear memory of keysight
    if bCareful:
        keysight.write("SOUR{}:DATA:VOL:CLEAR".format(int(chanNum+1)))
    if sys.version.startswith('2'):
        keysight.write_raw(bytes( "SOUR{}:DATA:ARB:DAC {}, {}".format(int(chanNum+1),name, binBlockHead))+ binBlockValues)
    else:
        keysight.write_raw(bytes( "SOUR{}:DATA:ARB:DAC {}, {}".format(int(chanNum+1),name, binBlockHead), 'ascii' )+ binBlockValues)
    if bSetAsOutput:
        keysight.write("SOUR{}:FUNC:ARB {}".format(int(chanNum+1),name))
    sleep(.2)

if __name__ == "__main__":    
    k = initialise()
##     sweep(k, 0.5*MHz, 1.5*MHz, 0.01, channel = 1)
##     
##     sleep(5)
##     off(k)

    t=np.linspace(0,1*10**-6,4096*20)
    y=np.sin(2*np.pi*t*10**6)

    uploadWaveform(k, y, name = '0test_sine', bSetAsOutput=True);
##     k.write("OUTP 1")
    #print(fg.handle.query("VOLT:OFFS?"))

    
    
##     t = np.linspace(0,2*np.pi,10)
##     amp_list = 2*np.sin(t)
##     arb(k,10*kHz,amp_list)
    

    