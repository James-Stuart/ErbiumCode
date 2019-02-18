#############BASIC FUNCTIONS OF THE HP4396A SPECTRUM ANALYSER#################
##############################MILOS RANCIC 2014###############################

import sys
from numpy import *
from ctypes import *
from time import clock
from visa import *
from struct import *
rm = ResourceManager()


#some usefull constants
Hz = 1
kHz = 10**3
MHz = 10**6
GHz = 10**9

#
def Introduction_to_Spectrum_Analyser_Commands():

#This programs retrieves data and communicates with the 
#HP4396A spectrum/network analyser. the following is a list of basic (usefull) commands.
#A full list of commands can be found in the reference guide.
#Note: adding a value to the end of some commands will determine the value sent to the 
#spectrum analyser, whilst adding '?' on the end will query the value from the
#spectrum analyser.


#CENT: centre frequency (Hz)

#SPAN: frequency span (Hz)

#STAR: start frequency (Hz)(alternative to centre/span)

#STOP: stop frequency (Hz) (alternative to centre/span)

#POWE: tracking generator output RF power (dBm)

#RFO ON|OFF: toggles tracking generator RF on and off

#SWET: sweep time (s)

#SWETAUTO ON|OFF: toggle between manual and automatic sweep time

#BW: resolution bandwidth (Hz)

#BWAUTO ON|OFF: toggle between manual and automatic resolution bandwidth


#these determine the form of data sent from the Spec An:
#FORM2: 32bit Float
#FORM3: 64bit Float
#FORM4: ascii string
#note that you must match the format that the Spec An
#sends with that recieved by pyVisa, nameley, single, double and ascii.
#for FORM2/3 (single/double) the data is send backwards (big_endian).

#MKR ON: turn on marker

#MKR OFF: turn off marker

#MKRSTAR: marker to start frequency

#MKRSTOP: marker to stop frequency

#SEAM MAX: move marker to maximum data value

#OUTPMKR?: command returns the marker value in the following order:
#primary part of data, secondary part of data, and sweep parameter

#OUTPDTRC?: retrieves the data trace arrays, (Signal strength, in dB)

#OUTPSWPRM?: retrieves the sweep parameters (RF frequency, in Hz)

#POIN: number of data points in trace (default max: 801)


#-----------------TRIGGERING-------------------#

#TRGS INT|EXT|VID|MAN|GAT: sets trigger source,
#options are internal, external, video, manual and gate.
#internal is the standard continuos trigger, external is ttl,
#video only works for zero span measurements, 

#the following list the trigger types
#HOLD: sweep hold, this freezes the data trace on the display, 
#the analyser stops sweeping and is in the hold "Hld" mode

#SING: single trigger, then returns to "Hld" mode

#NUMG: number of groups, triggers a specified number of sweeps, then
#returns to "Hld"

#CONT: continuous triggering (normal default state)

#TRGP POS|NEG: this determines trigger polarity, for example
#an external TTL signal can trigger off rising or falling edge.

#To set up the Spectrum analyser to return data only once a sweep has been
#completed, you need the following code:
#HP_SpecAn.write("CLES"): clears all the bits of the status and enable registers
#HP_SpecAn.write("*SRE 4; ESNB 1"): sets the correct bits in the registers
#to generate a service request (SRQ) when the scan has finished and the Spec An 
#returns to the hold (Hld) state
#HP_SpecAn.wait_for_srq(): this pauses execution of the python code and waits
#untill the Spec An the service request

    return;
#

#
def Initialise_HP_SpecAn():
    
    #This creates the intrument handle HP_SpecAn to talk to the spectrum analyser
    HP_SpecAn = rm.open_resource("GPIB0::20", timeout = 60000)
    
    #asks for 64bit precision data
    HP_SpecAn.write("FORM3")
    #ask Spectrum Analyser for its name
    HP_SpecAn.write("*IDN?")
    print ""
    print '-you are using the: ' + HP_SpecAn.read()
    
    #generates a boolean to say that its been initialised
    HP_Bool = 1
    
    return(HP_SpecAn, HP_Bool)
#


def HP_SpecAn_Centre_Span(centre, span, HP_SpecAn):
    #inputs span and centre frequencies to Spec An, and then queries the value
    #from the spectrum analyser for certainty
    HP_SpecAn.write("SPAN " + str(span))
    HP_SpecAn.write("CENT " + str(centre))
    actual_span = HP_SpecAn.query_ascii_values("SPAN?")
    actual_centre = HP_SpecAn.query_ascii_values("CENT?")
    
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


def HP_SpecAn_RF(tracking_gen, power, HP_SpecAn):
    #turns tracking generator RF power on and off and sets power level
    HP_SpecAn.write("RFO " + tracking_gen)
    actual_tracking_gen = HP_SpecAn.query_ascii_values("RFO?")
    if actual_tracking_gen[0] == 1:
        print 'The tracking generator is ON'
    else:
        print 'The tracking generator is OFF'
    
    #inputs RF power, then queries and checks for error
    HP_SpecAn.write("POWE " + str(power))
    actual_power = HP_SpecAn.query_ascii_values("POWE?")
    print 'The RF power is :  ' + str(actual_power[0]) + ' dBm'
    if actual_power[0] != power:
        variable_warning(actual_power[0], power, 'RF power')
    return(actual_tracking_gen[0], actual_power[0]) 
#

#
def HP_SpecAn_Trigger(trig_source, trig_type, trig_polarity, HP_SpecAn):
    #here we set up the trigger command, and query if its uploaded correctly
    #further, we que up the correct bits for a future serial request command
    

    
    #sets trigger source and queries to check
    HP_SpecAn.write("TRGS " + trig_source)
    HP_SpecAn.write("TRGS?")
    actual_trig_source = str(HP_SpecAn.read())
    
    HP_SpecAn.write(trig_type)
    
    #sets trigger polarity and queries to check
    HP_SpecAn.write("TRGP " + trig_polarity)
    HP_SpecAn.write("TRGP?")
    actual_trig_polarity = str(HP_SpecAn.read())

    if actual_trig_polarity[:-1] == trig_polarity and actual_trig_source[:-1] == trig_source:
        print "Spectrum Analyser Trigger Set"
    else:
        print "!#################################################################"
        print '>!Warning!! TRIGGER NOT SET'
        print "!#################################################################\n"
        del HP_SpecAn
        quit()
#

#
def HP_SpecAn_Resbandwidth_Sweeptime(resbandwidth, sweeptime, HP_SpecAn):
    
#this function inputs and returns the resolution bandwidth 
#from the spectrum Analyser
    #inputs resolution bandwidth, if required    
    if resbandwidth == 'AUTO':
        HP_SpecAn.write("BWAUTO ON")
        actual_resbandwidth = HP_SpecAn.query_ascii_values("BW?")
        print print_variable(actual_resbandwidth[0], 'the resolution bandwidth is: ')    
    
    else:
        #write desired resolution bandwidth
        HP_SpecAn.write("BWAUTO OFF; BW " + str(resbandwidth))
        #queries actuall resolution bandwidth, checks for consistency and prints
        actual_resbandwidth = HP_SpecAn.query_ascii_values("BW?")
        print print_variable(actual_resbandwidth[0], 'the resolution bandwidth is: ')
        if actual_resbandwidth[0] != resbandwidth:
            variable_warning(actual_resbandwidth[0], resbandwidth, 'resolution bandwidth')
    
    if sweeptime == 'AUTO':
        HP_SpecAn.write("SWETAUTO ON")
        actual_sweeptime = HP_SpecAn.query_ascii_values("SWET?")
        print 'The sweeptime is :  ' + str(actual_sweeptime[0]*1000) + ' ms'
    else:
        #writes desired sweeptime
        HP_SpecAn.write("SWETAUTO OFF; SWET " + str(sweeptime))
        #queries actual sweeptime, checks for consistency and prints
        actual_sweeptime = HP_SpecAn.query_ascii_values("SWET?")
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
