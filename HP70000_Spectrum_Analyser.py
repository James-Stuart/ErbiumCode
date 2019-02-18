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
def Initialise_HP70000_SpecAn():
    
    #This creates the intrument handle HP70000_SpecAn to talk to the spectrum analyser
    HP70000_SpecAn = rm.open_resource("GPIB0::18", timeout = 30000)
    
    HP70000_SpecAn.write_termination = ';'
    #asks for 64bit precision data
    HP70000_SpecAn.write("TDF B")
    #ask Spectrum Analyser for its name
    HP70000_SpecAn.write("ID?")
    print ""
    print '-you are using the: HP ' + HP70000_SpecAn.read()
    
    #generates a boolean to say that its been initialised
    HP_Bool = 1
    
    return(HP70000_SpecAn, HP_Bool)
#


def HP70000_SpecAn_Centre_Span(centre, span, HP70000_SpecAn):
    #inputs span and centre frequencies to Spec An, and then queries the value
    #from the spectrum analyser for certainty
    HP70000_SpecAn.write("SP " + str(span) + 'HZ')
    HP70000_SpecAn.write("CF " + str(centre) + 'HZ')
    actual_span = HP70000_SpecAn.query_ascii_values("SP?")
    actual_centre = HP70000_SpecAn.query_ascii_values("CF?")
    
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


def HP70000_SpecAn_RF(tracking_gen, power, HP70000_SpecAn):
    #turns tracking generator RF power on and off and sets power level
    HP70000_SpecAn.write("SRCPWR " + tracking_gen)
    actual_tracking_gen = HP70000_SpecAn.query_ascii_values("SRCPWR?")
    if actual_tracking_gen[0] == 1:
        print 'The tracking generator is ON'
    else:
        print 'The tracking generator is OFF'
    
    #inputs RF power, then queries and checks for error
    HP70000_SpecAn.write("SRCPWR " + str(power) + 'DBM')
    actual_power = HP70000_SpecAn.query_ascii_values("SRCPWR?")
    print 'The RF power is :  ' + str(actual_power[0]) + ' dBm'
    if actual_power[0] != power:
        variable_warning(actual_power[0], power, 'RF power')
    return(actual_tracking_gen[0], actual_power[0]) 
#

#
def HP70000_SpecAn_Trigger(trig_source, trig_type, HP70000_SpecAn):
    #here we set up the trigger command, and query if its uploaded correctly
    #further, we que up the correct bits for a future serial request command
    
    
    #sets trigger source and queries to check
    HP70000_SpecAn.write("TM " + trig_source)
    HP70000_SpecAn.write("TM?")
    actual_trig_source = str(HP70000_SpecAn.read())
    
    HP70000_SpecAn.write(trig_type)

    if actual_trig_source[:-1] == trig_source:
        print "Spectrum Analyser Trigger Set"
    else:
        print "!#################################################################"
        print '>!Warning!! TRIGGER NOT SET'
        print "!#################################################################\n"
        del HP70000_SpecAn
        quit()
#

#
def HP70000_SpecAn_Resbandwidth_Sweeptime(resbandwidth, sweeptime, HP70000_SpecAn):
    
#this function inputs and returns the resolution bandwidth 
#from the spectrum Analyser
    #inputs resolution bandwidth, if required    
    if resbandwidth == 'AUTO':
        HP70000_SpecAn.write("RB AUTO")
        actual_resbandwidth = HP70000_SpecAn.query_ascii_values("RB?")
        print print_variable(actual_resbandwidth[0], 'the resolution bandwidth is: ')    
    
    else:
        #write desired resolution bandwidth
        HP70000_SpecAn.write("RB " + str(resbandwidth) + 'HZ')
        #queries actuall resolution bandwidth, checks for consistency and prints

        actual_resbandwidth = HP70000_SpecAn.query_ascii_values("RB?")
        print print_variable(actual_resbandwidth[0], 'the resolution bandwidth is: ')
        if actual_resbandwidth[0] != resbandwidth:
            variable_warning(actual_resbandwidth[0], resbandwidth, 'resolution bandwidth')
    
    if sweeptime == 'AUTO':
        HP70000_SpecAn.write("ST AUTO")
        actual_sweeptime = HP70000_SpecAn.query_ascii_values("ST?")
        print 'The sweeptime is :  ' + str(actual_sweeptime[0]*1000) + ' ms'
    else:
        #writes desired sweeptime
        HP70000_SpecAn.write("ST " + str(sweeptime) + 'S')
        #queries actual sweeptime, checks for consistency and prints
        actual_sweeptime = HP70000_SpecAn.query_ascii_values("ST?")
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
