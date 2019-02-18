######BASIC FUNCTIONS OF THE AGILENT 86142B OPTICAL SPECTRUM ANALYSER###########
###########################MILOS RANCIC 2014####################################

from numpy import *
from ctypes import *
from time import clock
from visa import *
from struct import *
rm = ResourceManager()

def Initialise_OSA():
    

    #gets an instrument handle from the agilent OSA
    Agilent_OSA = rm.open_resource("GPIB::23",timeout = 500000)
    Agilent_OSA_write("INIT:CONT ON", Agilent_OSA)
    identity = Agilent_OSA_write("*IDN?", Agilent_OSA)
    print ""
    print '-You are using the: ' + str(identity)
    
    #generates a boolean to say that its been initialised
    Agilent_bool = 1
    
    return(Agilent_OSA, Agilent_bool)
#

#
def OSA_record_drift(Agilent_OSA):
    wavelength_data = []
    Agilent_OSA_write("INIT:CONT OFF", Agilent_OSA)

    for i in range(10):
        Agilent_OSA_write("INIT:IMM", Agilent_OSA)
        Agilent_OSA_write("CALC:MARK:MAX", Agilent_OSA)
        data = Agilent_OSA.query_ascii_values("CALC:MARK1:X?")
        wavelength_data.append(data[0])
    Agilent_OSA_write("INIT:CONT ON", Agilent_OSA)

    #the following code determines the mean of the data (in nm), as well as the
    #standard deviation (std) in MHz, and the difference between the furthest two
    #data samples in pm
    mean_wavelength = mean(wavelength_data)*(10**9)
    std_wavelength= std(wavelength_data)*(10**12)
    var = (max(wavelength_data) - min(wavelength_data))*(10**12)
    wavelength_change_MHz = (195.23700-mean_wavelength*0.12706)*(10**6)

    print "largest variance is: " + str(var) + " pm"
    print "the mean is: " + str(mean_wavelength) + " nm"
    print "the mean is: " + str(mean_wavelength*0.12706) + " THz"
    print "the standard deviation is: " + str(std_wavelength*127.06) + " MHz"
    print wavelength_change_MHz

    
#

#
def Agilent_OSA_write(write_command, Agilent_OSA):
#because the Agilent OSA is special, it tries to execute commands before 
#the previous command has completed, which causes it to lock up occasionally
#To prevent this, each command write sent to the OSA needs to be followed by an
# *OPC? query, which checks if the previous command has completed.
#So instead of sending commands via the Agilent_OSA.write() function (the inbuilt
#visa function, commands should instead be sent via the Agilent_OSA_write()
#function i have written below

    var = []
    Agilent_OSA.write(write_command)
    if write_command[-1] == "?":
        var = Agilent_OSA.read()
    else:    
        Agilent_OSA.write("*OPC?")
        check_if_written = int(Agilent_OSA.read())
        if check_if_written != 1:
            print write_command + " has not sent"
            Agilent_OSA.write("INIT:CONT ON")
            quit()
    return(var)

#

#
def OSA_find_peak(Agilent_OSA):

    #Zero's in on laser wavelength by slowly reducing scan range
    #and centering the highest peak in the middle of the spectrum
    #single sweeps performed between each operator to ensure correct behavior
    #the following line turns of continuous sweeping, otherwise the single sweep
    #command "INIT:IMM" will be ignored
    Agilent_OSA_write("INIT:CONT OFF", Agilent_OSA)
    #the following command initiates a single sweep
    Agilent_OSA_write("INIT:IMM", Agilent_OSA)

    #this sets the the OSA span to maximum, so that we dont miss our laser wavelength
    Agilent_OSA_write("SENS:WAV:SPAN 1000nm", Agilent_OSA)
    #OSA sweeps once
    Agilent_OSA_write("INIT:IMM", Agilent_OSA)
    #the following command sends the marker to the maximum signal level
    #which is hopefully our laser light
    Agilent_OSA_write("CALC:MARK:MAX", Agilent_OSA)
    #OSA sweeps again
    Agilent_OSA_write("INIT:IMM", Agilent_OSA)
    #this then sends the marker to the centre value
    Agilent_OSA_write("CALC:MARK:SCEN", Agilent_OSA)
    Agilent_OSA_write("INIT:IMM", Agilent_OSA)
    
    #rinse and repeat, so that we eventually narrow down to the minimum span
    Agilent_OSA_write("SENS:WAV:SPAN 30nm", Agilent_OSA)
    Agilent_OSA_write("INIT:IMM", Agilent_OSA)
    Agilent_OSA_write("CALC:MARK:MAX", Agilent_OSA)
    Agilent_OSA_write("INIT:IMM", Agilent_OSA)
    Agilent_OSA_write("CALC:MARK:SCEN", Agilent_OSA)
    Agilent_OSA_write("INIT:IMM", Agilent_OSA)
    Agilent_OSA_write("SENS:WAV:SPAN 1nm", Agilent_OSA)
    Agilent_OSA_write("INIT:IMM", Agilent_OSA)
    Agilent_OSA_write("CALC:MARK:MAX", Agilent_OSA)
    Agilent_OSA_write("INIT:IMM", Agilent_OSA)
    Agilent_OSA_write("CALC:MARK:SCEN", Agilent_OSA)
    Agilent_OSA_write("INIT:IMM", Agilent_OSA)
    
    #this command sets the scale to linear, so that the 
    #centre value is more obvious
    Agilent_OSA_write("DISP:WIND:TRAC:Y:SCAL:SPAC LIN", Agilent_OSA)
    Agilent_OSA_write("INIT:IMM", Agilent_OSA)
    Agilent_OSA_write("CALC:MARK:MAX", Agilent_OSA)
    Agilent_OSA_write("INIT:IMM", Agilent_OSA)
    Agilent_OSA_write("SENS:WAV:SPAN 0.2nm", Agilent_OSA)
    Agilent_OSA_write("INIT:IMM", Agilent_OSA)
    Agilent_OSA_write("CALC:MARK:MAX", Agilent_OSA)
    Agilent_OSA_write("INIT:IMM", Agilent_OSA)
    Agilent_OSA_write("CALC:MARK:SCEN", Agilent_OSA)
    Agilent_OSA_write("INIT:IMM", Agilent_OSA)
    
    #the following command reads the marker 1 signal level
    #and then sets the reference level on the trace to 1.1 times the signal
    #level, so that the laser signal now takes up the entire image trace
    light_level = Agilent_OSA.query_ascii_values("CALC:MARK1:Y?")
    light_level = light_level[0]
    Agilent_OSA_write("DISP:WIND:TRAC:Y:SCAL:RLEV " + str(light_level*1.1),Agilent_OSA)

    Agilent_OSA_write("INIT:CONT ON",Agilent_OSA)





#

#
def OSA_measure_wavelength(Agilent_OSA):
    #this function records the wavelength of the laser 10 times
    #and returns the average of those measurements as the laser wavelength
    wavelength_data = []
    Agilent_OSA_write("INIT:CONT OFF", Agilent_OSA)

    for i in range(10):
        Agilent_OSA_write("INIT:IMM", Agilent_OSA)
        Agilent_OSA_write("CALC:MARK:MAX", Agilent_OSA)
        data = Agilent_OSA.query_ascii_values("CALC:MARK1:X?")
        wavelength_data.append(data[0])
    Agilent_OSA_write("INIT:CONT ON", Agilent_OSA)
    mean_wavelength = mean(wavelength_data)*(10**9)
    return(mean_wavelength)

def OSA_fast_measure_wavelength(Agilent_OSA):
    Agilent_OSA_write("CALC:MARK:MAX", Agilent_OSA)
    Agilent_OSA_write("CALC:MARK:SCEN", Agilent_OSA)
    wavelength = Agilent_OSA.query_ascii_values("CALC:MARK1:X?")
    return(wavelength[0])
        
        