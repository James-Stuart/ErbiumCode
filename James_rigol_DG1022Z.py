import visa 
kHz = 10**3
MHz = 10**6
GHz = 10**9

def initialise_DG1022Z():
    
    rm = visa.ResourceManager()
    rigol =  rm.open_resource('USB0::0x1AB1::0x0642::DG1ZA193403359::INSTR')
    print 'Hello, my name is:' 
    print rigol.query('*IDN?') + 'But you can call me DG1022Z'
    return rigol
#


#
def linear_sweep(rigol, start, stop, time):
    ''' Creates a simple linear sweep at the given start and stop frequencies for
    a given sweep time'''
    start_com = 'FREQ:STAR ' + str(start)
    stop_com = 'FREQ:STOP ' + str(stop)
    time_com = 'FREQ:TIME ' + str(time)
    
    rigol.write(start_com)
    rigol.write(stop_com)
    rigol.write(time_com)
    rigol.write('SWE:SPAC LIN')#Sweep time LINear
    rigol.write('SWE:STAT ON') #Sweep status ON (or OFF)
    rigol.write('OUTP ON')     #OUTPut ON (OFF)
#   


#
def sweep_off(rigol):
    ''' It turns the sweeping off...
    ...
    ...'''
    rigol.write('SWE:STAT OFF')
#


#
def waveform(rigol, channel = 'CH1', wavetype = 'SIN', freq = 1*kHz, amp = 1, offset = 0):
    ''' Creates a simple preset waveform with all kinds of optional variables.
    '''
    waveform_types = ['SIN','SQU','RAMP','PULS','NOIS']
    if wavetype in waveform_types:
        pass
    else:
        raise error("Wavetype must be ['SIN','SQU','RAMP','PULS','NOIS']")
    
    if channel == 'CH1':
        command = 'APPL:' + wavetype + ' ' + str(freq) + ',' + str(amp) + ',' +str(offset)
    elif channel == 'CH2':
        command = 'APPL:' + wavetype + ':CH2 ' + str(freq) + ',' + str(amp) + ',' +str(offset)
    else:
        raise error('Channel must be either CH1 or CH2')
    rigol.write(command)
#


#
def arb(rigol):
    ''' Work in progress 
    Vertical resolution of user defined wave is 14 bits int between, 0 - 16383
    corresponding to minimum and maximum amplitudes'''
    
    
    rigol.write('FUNC USER')
    rigol.write('FREQ 1000') #Sets the freq of the waveform (i.e. the time 
                             #between data point = 1/(freq*number_of_data_points)
    rigol.write('VOLT:UNIT VPP')
    rigol.write('VOLT:HIGH 4')
    rigol.write('VOLT:LOW -4')
    rigol.write('DATA:DAC VOLATILE,8192,16383,8192,0')
    rigol.write('FUNC:USER VOLATILE')
#

def calc(r):
    ''' Temperature in sample space based on resistance on thermistors '''
    z = (r - 66)/22
    temp = 0.016*z**4 - 0.03*z**3 - 0.0046*z**2 -0.2*z + 1.7
    print temp


#
if __name__ == "__main__":
##     rigol = initialise_DG1022Z()
##     linear_sweep(rigol,1000,10000,1)
##     sweep_off(rigol)
##     waveform(rigol,'CH1','SQU',2*kHz,2,1)
##     arb(rigol)
    calc(410)
        
    
    