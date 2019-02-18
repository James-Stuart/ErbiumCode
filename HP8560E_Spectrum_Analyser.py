#############BASIC FUNCTIONS OF THE HP4396A SPECTRUM ANALYSER#################
##############################MILOS RANCIC 2014###############################

import sys
from numpy import *
from ctypes import *
from time import clock
from time import sleep
from visa import *
from struct import *
rm = ResourceManager()


#some usefull constants
Hz = 1
kHz = 1e3
MHz = 1e6
GHz = 1e9

#
def Introduction_to_Spectrum_Analyser_Commands():



#-----------------TRIGGERING-------------------#

#TRGS FREE|EXT|VID|LIN: sets trigger source,
#options are internal (free run), external, video or line.
#internal is the standard continuos trigger, external is ttl,
#video only works for zero span measurements, 

#FOR trigger type, you can choose from
#'SNGLS' for single or 
#'CONTS' for continuous triggering.


    return;
#

#
def Initialise_HP8560E_SpecAn():
    
    #This creates the intrument handle HP8560E_SpecAn to talk to the spectrum analyser
    HP8560E_SpecAn = rm.open_resource("GPIB0::18", timeout = 15000)
    
    HP8560E_SpecAn.write_termination = ';'
    #asks for 64bit precision data
    HP8560E_SpecAn.write("TDF B")
    #ask Spectrum Analyser for its name
    HP8560E_SpecAn.write("ID?")
    HP8560E_SpecAn.read()
##     print '-you are using the: HP ' + HP8560E_SpecAn.read()
    
    #generates a boolean to say that its been initialised
    HP_Bool = 1
    
    return(HP8560E_SpecAn, HP_Bool)
#


def HP8560E_SpecAn_Centre_Span(centre, span, HP8560E_SpecAn):
    #inputs span and centre frequencies to Spec An, and then queries the value
    #from the spectrum analyser for certainty
    HP8560E_SpecAn.write("SP " + str(span) + 'HZ')
    HP8560E_SpecAn.write("CF " + str(centre) + 'HZ')
    actual_span = HP8560E_SpecAn.query_ascii_values("SP?")
    actual_centre = HP8560E_SpecAn.query_ascii_values("CF?")
    
    #prints values returned from Spec An, and gives warning if
    #it does not match expected values
    print print_variable(actual_span[0], 'the spectrum span is: ')
    if actual_span[0] != span:
        variable_warning(actual_span[0], span, 'spectrum span')
        
    print print_variable(actual_centre[0], 'the centre frequency is: ')
    if actual_centre[0] != centre:
        variable_warning(actual_centre[0], centre, 'centre frequency')
    return(actual_centre[0], actual_span[0])
#


def HP8560E_SpecAn_RF(tracking_gen, power, HP8560E_SpecAn):
    #turns tracking generator RF power on and off and sets power level
    print "power is: " + str(power)
    HP8560E_SpecAn.write('SRCPWR ' + str(power))
    HP8560E_SpecAn.write('SRCPWR?')
    actual_tracking_gen = HP8560E_SpecAn.read()
    print(actual_tracking_gen)
    if actual_tracking_gen[0] == 1:
        print 'The tracking generator is in a super position of OFF and ON'
    else:
        print 'The tracking generator is in a super position of OFF and ON'
    
    #inputs RF power, then queries and checks for error
    HP8560E_SpecAn.write("SRCPWR " + str(power) + 'DBM')
    actual_power = HP8560E_SpecAn.query_ascii_values("SRCPWR?")
    print 'The RF power is :  ' + str(actual_power[0]) + ' dBm'
##     if actual_power[0] != power:
##         variable_warning(actual_power[0], power, 'RF power')
    return(actual_tracking_gen[0], actual_power[0]) 
#

#
def HP8560E_SpecAn_Trigger(trig_source, trig_type, HP8560E_SpecAn):
    #here we set up the trigger command, and query if its uploaded correctly
    #further, we que up the correct bits for a future serial request command
    
    
    #sets trigger source and queries to check
    HP8560E_SpecAn.write("TM " + trig_source)
    HP8560E_SpecAn.write("TM?")
    actual_trig_source = str(HP8560E_SpecAn.read())
    
    HP8560E_SpecAn.write(trig_type)

    if actual_trig_source[:-1] == trig_source:
        print "Spectrum Analyser Trigger Set"
    else:
        print "!#################################################################"
        print '>!Warning!! TRIGGER NOT SET'
        print "!#################################################################\n"
        del HP8560E_SpecAn
        quit()
#

#
def HP8560E_SpecAn_Resbandwidth_Sweeptime(resbandwidth, sweeptime, HP8560E_SpecAn):
    
#this function inputs and returns the resolution bandwidth 
#from the spectrum Analyser
    #inputs resolution bandwidth, if required    
    if resbandwidth == 'AUTO':
        HP8560E_SpecAn.write("RB AUTO")
        actual_resbandwidth = HP8560E_SpecAn.query_ascii_values("RB?")
        print print_variable(actual_resbandwidth[0], 'the resolution bandwidth is: ')    
    
    else:
        #write desired resolution bandwidth
        HP8560E_SpecAn.write("RB " + str(resbandwidth) + 'HZ')
        #queries actuall resolution bandwidth, checks for consistency and prints

        actual_resbandwidth = HP8560E_SpecAn.query_ascii_values("RB?")
        print print_variable(actual_resbandwidth[0], 'the resolution bandwidth is: ')
        if actual_resbandwidth[0] != resbandwidth:
            variable_warning(actual_resbandwidth[0], resbandwidth, 'resolution bandwidth')
    
    if sweeptime == 'AUTO':
        HP8560E_SpecAn.write("ST AUTO")
        actual_sweeptime = HP8560E_SpecAn.query_ascii_values("ST?")
        print 'The sweeptime is :  ' + str(actual_sweeptime[0]*1000) + ' ms'
    else:
        #writes desired sweeptime
        HP8560E_SpecAn.write("ST " + str(sweeptime) + 'S')
        #queries actual sweeptime, checks for consistency and prints
        actual_sweeptime = HP8560E_SpecAn.query_ascii_values("ST?")
        print 'The sweeptime is :  ' + str(actual_sweeptime[0]*1000) + ' ms'
        if actual_sweeptime[0] != sweeptime:
            variable_warning(actual_sweeptime[0], sweeptime, 'The Sweeptime')
    
    return(actual_resbandwidth[0], actual_sweeptime[0])
#

#
def print_variable(variable, variable_statement):
#this function determines the length of the returned frequency variable
#then prints a statement with the appropriate units 
#(Hz, kHz, MHz, or GHz) depending on its
#length. Usually called for things like span, bandwidth, centre frequency, etc

    length = len(str(int(variable)))
    if 1 <= length <= 3:
            statement = variable_statement + str(variable) + ' Hz' 
    elif 4 <= length <= 6:
            statement = variable_statement + str(variable/kHz) + ' kHz'
    elif 7 <= length <= 9:
            statement = variable_statement + str(variable/MHz) + ' MHz'
    elif 10 <= length <= 12:
            statement = variable_statement + str(variable/GHz) + ' GHz'
            
    return(statement)
#

#
def variable_warning(actual_variable, expected_variable, variable_name):
#this function checks variables returned from the equiptment against
#the variables set, to ensure that there has not been a mistake


    print "!#################################################################"
    if expected_variable > actual_variable:
        print '>!Warning!! ' + variable_name + ' is smaller than desired'
    elif expected_variable < actual_variable:
        print '>!Warning!! ' + variable_name + ' is greater than desired!'
        
    print "!#################################################################\n"

#
#[HP8560E_SpecAn,bool] = Initialise_HP8560E_SpecAn()

#MORGANs CHANGES
def convert2db(SpecAn, data):
    #Traces are made up of 601 points (x axis) with a value from 0 to 610
    #This can be converted into dB
    SpecAn.write('LG?')
    dB_div = float(SpecAn.read())
    entire_depth = 10*dB_div #how many dB in the entire display
    SpecAn.write('RL?') #Get the reference level
    ref_level = float(SpecAn.read())
    
    lowest_point = ref_level - entire_depth 
    #To convert Y data to dB -> y_data*entire_depth/610 + lowest_point  

    db_data = data*entire_depth/610 + lowest_point #Convert to dB
    return(db_data)

def HP8560E_GetXAxis(SpecAn):
    SpecAn.write('SP?')
    span = float(SpecAn.read())  
    SpecAn.write('CF?')
    centre = float(SpecAn.read())
    return np.arange(centre-span/2, centre+span/2, span/601)
    
def HP8560E_GetTraceSimple(SpecAn, bAsLinear = True):
    SpecAn.write('TRA?')
    binary = SpecAn.read_raw()
    raw_data = np.frombuffer(binary, '>u2') # Data format is big-endian unsigned integers
    datDB = convert2db(SpecAn, raw_data)
    
    if bAsLinear:
        return 10**(datDB/10.)
    else:
        return datDB
    
def HP8560E_WaitForExtTrig(SpecAn):
    HP8560E_SpecAn_Trigger('EXT', 'SNGLS', SpecAn)
    #sets up registers to return interupt when sweep is complete
    SpecAn.write("CLEAR; RQS 4") 

def HP8560E_FreeRun(SpecAn):
    HP8560E_SpecAn_Trigger("FREE", 'CONTS', SpecAn)

def HP8560E_GetTraceTriggered(SpecAn, bAsLinear = True, waitForMs=3000, bRetXAxis=True):
    HP8560E_WaitForExtTrig(SpecAn)
    SpecAn.write('TS')
    #Waits for Spectrum Analyser to finish Data sweep
    SpecAn.wait_for_srq(timeout = waitForMs)
    data  = HP8560E_GetTraceSimple(SpecAn, bAsLinear)
    
    #HP8560E_SpecAn_Trigger("FREE", 'CONTS', SpecAn)
    if bRetXAxis:
        return data, HP8560E_GetXAxis(SpecAn)
    else:
        return data


