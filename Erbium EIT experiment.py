import sys
from numpy import *
from ctypes import *
from matplotlib import *
from visa import *
from struct import *
from windfreakV2 import *
#from HP_Spectrum_Analyser import *
from Agilent_OSA import *
from Arduino_Pulseblaster_SpecAn_Trench import *
from Rigol_DMM import *
from Burleigh_Wavemeter import *
from E4402B_Spectrum_Analyser import *


import os
import pylab

from matplotlib.widgets import CheckButtons


#some usefull constants
Hz = 1
kHz = 10**3
MHz = 10**6
GHz = 10**9


us=10**-6;
ms=10**-3;
s=1;

#the following booleans determine if the the corresponding equiptment is being used
#they return a 1 when the equiptment is initialised, otherwise they return 0.
#this is neccesary so that you can close the correct visa sessions when you 
#want to quit the program

global HP_SpecAn_Bool
global Burleigh_WM_Bool
global Rigol_DMM_Bool
global Agilent_OSA_Bool
global WindfreakV2_Bool

HP_SpecAn_Bool = 0
Rigol_DMM_Bool = 0
Agilent_OSA_Bool = 0
WindfreakV2_Bool = 0
Burleigh_WM_Bool = 0


laser_wavelength = 'Not Queried'
SpecAn_BW = 'Not Queried'
SpecAn_Centre = 'Not Queried'
SpecAn_Span = 'Not Queried'
SpecAn_Sweeptime = 'Not Queried'
SpecAn_Power = 'Not Queried'
windfreak_freq = 0
windfreak_HILO = 'Not Queried'
windfreak_level = 'Not Queried'


arduino_comport = 'COM10'

#----------HP 4396A Spectrum/Network Analyser Global Variables-----------------#

#IMPORTANT: there is a 16.3 ms delay between triggering the Spectrum Analyser
#and beginning a scan. Hence the spectrum analyser should be triggered ahead
#of RF to achieve the desired delay

#input the spectrum span and centre frequency in Hz
span = 500*MHz
centre = 1500*MHz

#input whether to turn on tracking generator and specify the RF power in dBm
tracking_gen = 'ON'  #accepts 'ON' or 'OFF'
RF_power = -10 #in dBm


#inputs triggering options, see "Intro to Spec An commands"
trig_source = "EXT"
trig_type = "SING"
trig_polarity = "POS"
#input the sweeptime and resolution bandwidth, otherwise set to AUTO
sweeptime =  30*ms #in seconds, otherwise set to 'AUTO'
resbandwidth = 30*kHz # in Hz, otherwise set to 'AUTO'




def save_data(filename, SpecAn_BW, SpecAn_Sweeptime, SpecAn_Centre, SpecAn_Span, 
    laser_wavelength, windfreak_freq, windfreak_level, windfreak_HILO, x_axis_data, y_axis_data, temp):
    
    
    
    day = time.strftime("%d")
    month = time.strftime("%m")
    year = time.strftime("%Y")
    hour = time.strftime("%H")
    minute = time.strftime("%M")
    second = time.strftime("%S")
    
    date_string = day + "_" + month + "_" + year
    time_string = hour + "Hrs " + minute + "Mins " + second + "Secs"
    
    filepathA = "C:\Users\Milos\Desktop\EIT Data\\" + date_string

    if not os.path.exists(filepathA):
        os.mkdir(filepathA)
        
    filepathB = "C:\Users\Milos\Desktop\EIT Data\\" + date_string + "\\-10dbm-30ms pulse"

    if not os.path.exists(filepathB):
        os.mkdir(filepathB)
        
    filepath = "C:\Users\Milos\Desktop\EIT Data\\" + date_string + "\\-10dbm-30ms pulse\data"

    if not os.path.exists(filepath):
        os.mkdir(filepath)
        
    location = filepath + "\\" + filename + ".txt"
    OutputFile = open(location, 'w')
    OutputFile.write("The Date is: " + date_string + "\n")
    OutputFile.write("The Time is: " + time_string + "\n")
    OutputFile.write(print_variable(SpecAn_BW,"The Spectrum Analyser resolution bandwidth is: ") + "\n")
    OutputFile.write(str(SpecAn_BW)+"\n")
    OutputFile.write("The Spectrum Analyser sweeptime is: " + str(SpecAn_Sweeptime*1000) + " ms\n")
    OutputFile.write(str(SpecAn_Sweeptime)+"\n")
    OutputFile.write(print_variable(SpecAn_Centre,"The Spectrum Analyser centre frequency is: ") + "\n")
    OutputFile.write(str(SpecAn_Centre)+"\n")    
    OutputFile.write(print_variable(SpecAn_Span,"The Spectrum Analyser span is: ") + "\n")
    OutputFile.write(str(SpecAn_Span)+"\n")   
    OutputFile.write("The laser wavelength is: " + str(laser_wavelength) +  " nm \n")
    OutputFile.write(str(laser_wavelength)+"\n")
    OutputFile.write("The sample space temperature is: " + str(temp) + " K\n")
    OutputFile.write(str(temp)+"\n")

  
    
    for i in range(len(x_axis_data)):
        OutputFile.write(str(x_axis_data[i]) + ",  " +str(y_axis_data[i])+"\n")
    
#     


def main_loop():
    
    #the following sets python to interactive mode so that we can see the spectrum analyser
    #output as a GUI
    pylab.ion()
    
    #initialises required equipment    
    global HP_SpecAn_Bool
    global Rigol_DMM_Bool
    global Agilent_OSA_Bool
    global Burleigh_WM
    
    global HP_SpecAn
    global Rigol_DMM
    global Agilent_OSA
    global Burleigh_WM_Bool
    
    [HP_SpecAn, HP_SpecAn_Bool] = Initialise_HP_SpecAn()
    #[Burleigh_WM, Burleigh_WM_Bool] = Initialise_Burleigh_WM()
    [Rigol_DMM, Rigol_DMM_Bool] = Initialise_DMM()
    [Agilent_OSA, Agilent_OSA_Bool] = Initialise_OSA()

    #ensure that both the windfreak power and hp tracking generator are off
    #before you initialise the Arduino, because this will reset the arduino
    #and will let RF through the RF switches


    #sends necessary pre-data collection settings to the Spectrum Analyser
    #and uploads desired pulse sequence to the RadioProcessor
    [SpecAn_BW, SpecAn_Sweeptime] = HP_SpecAn_Resbandwidth_Sweeptime(resbandwidth, sweeptime, HP_SpecAn)
    [SpecAn_Centre, SpecAn_Span] = HP_SpecAn_Centre_Span(centre, span, HP_SpecAn)
    [SpecAn_track, SpecAn_Power] = HP_SpecAn_RF(tracking_gen, RF_power, HP_SpecAn)
    #laser_wavelength = Burleigh_WM.ask_for_values("FETC:SCAL:WAV?")
    laser_wavelength = OSA_measure_wavelength(Agilent_OSA)
        
    Arduino = Initialise_Arduino(arduino_comport)
    time.sleep(1)
    
    #the i loop repeats the data set
    for i in range (1,21):

        #measure and record sample temperature 
        [resistance, temp] = Rigol_DMM_Measure_Resistance(Rigol_DMM)

        #sets up registers for data reading
        HP_SpecAn.write("CLES; *SRE 4; ESNB 1")
        #triggers spectrum analyser for data reading
        HP_SpecAn_Trigger(trig_source, trig_type, trig_polarity, HP_SpecAn)


        #need to wait a bit (100ms) for spectrum analyser trigger to set before
        #we can start the pulse program, otherwise spectrum analyser gets
        #stuck waiting for trigger because it missed it
        time.sleep(0.1)
        Arduino.write('0')
        pulse_sequence =  Arduino.read()
        
        #the following if statement verifies that the pulse sequence executed
        #is the correct one
        
        if (pulse_sequence == "EIT test program complete"):
            print 'pulse sequence verified and executed'
        else:
            print 'incorrect pulse sequence'
            exit_button(1)
        
        
        #Waits for Spectrum Analyser to finish Data sweep
        HP_SpecAn.wait_for_srq()
        

        x_axis_data = HP_SpecAn.ask_for_values("OUTPSWPRM?",double | big_endian)
        y_axis_data = HP_SpecAn.ask_for_values("OUTPDTRC?",double | big_endian)
        
        filename =  "EIT 7A field, run " + str(i)

        save_data(filename, SpecAn_BW, SpecAn_Sweeptime, SpecAn_Centre, SpecAn_Span, 
        laser_wavelength, windfreak_freq, windfreak_level, windfreak_HILO, x_axis_data, y_axis_data, temp)
        
        
        display_start = 10
        display_end = 790
        data_plot_window(x_axis_data,y_axis_data, resistance, temp, filename, display_start, display_end)

        #turns off the RF and returns the spectrum analyser back to normal state.
        #Windfreak_ONOFF(0, query_state, WindfreakV2)
    
    del Arduino
    
    HP_SpecAn_Trigger('INT', 'CONT', trig_polarity, HP_SpecAn)
#


def test():
    
    [HP_SpecAn, HP_SpecAn_Bool] = Initialise_HP_SpecAn()
    Arduino = Initialise_Arduino(arduino_comport)
    


    #sends necessary pre-data collection settings to the Spectrum Analyser

    [SpecAn_BW, SpecAn_Sweeptime] = HP_SpecAn_Resbandwidth_Sweeptime(resbandwidth, sweeptime, HP_SpecAn)
    [SpecAn_Centre, SpecAn_Span] = HP_SpecAn_Centre_Span(centre, span, HP_SpecAn)
    [SpecAn_track, SpecAn_Power] = HP_SpecAn_RF(tracking_gen, RF_power, HP_SpecAn)
    
    
    Arduino.write('0')
    val = Arduino.read()
    
    #this if statement determines if the correct .ino file is loaded onto the 
    #arduino, and loads the freerun.ino if neccesary
    if (val != 'holeburning test program complete'):
        
        #the arduino has the wrong .ino file so we must delete the visa handle in 
        #in order to upload the correct program
        del Arduino
        Upload_Arduino('EIT_test_program')
        #once we start uploading the new script to the arduino, we need to wait 
        #12 seconds for it to complete
        time.sleep(12)
        
        #we now regenerate the handle and open the correct RF channels for the
        #spectrum analyser by starting the 'pulse sequence'
        Arduino = Initialise_Arduino('COM10')
    

    #sets up registers for data reading
    HP_SpecAn.write("CLES; *SRE 4; ESNB 1")
    #triggers spectrum analyser for data reading
    HP_SpecAn_Trigger(trig_source, trig_type, trig_polarity, HP_SpecAn)

    #need to wait 100ms for spectrum analyser trigger to set before
    #we can start the pulse program, otherwise spectrum analyser gets
    #stuck waiting for trigger because it missed it
    time.sleep(0.1)
 
    Arduino.write('0')
    print Arduino.read()
    
    #Waits for Spectrum Analyser to finish Data sweep
    HP_SpecAn.wait_for_srq()

    x_axis_data = HP_SpecAn.ask_for_values("OUTPSWPRM?",double | big_endian)
    y_axis_data = HP_SpecAn.ask_for_values("OUTPDTRC?",double | big_endian)
    plot(x_axis_data[10:701], y_axis_data[10:701])
    show()
    #turns off the RF and returns the spectrum analyser back to normal state.
    #Windfreak_ONOFF(0, query_state, WindfreakV2)
    HP_SpecAn_Trigger('INT', 'CONT', trig_polarity, HP_SpecAn)
#


def loop_test():
    
    global HP_SpecAn_Bool
    global HP_SpecAn
    pylab.ion()
    [HP_SpecAn, HP_SpecAn_Bool] = Initialise_HP_SpecAn()
    Arduino = Initialise_Arduino(arduino_comport)
    


    #sends necessary pre-data collection settings to the Spectrum Analyser

    [SpecAn_BW, SpecAn_Sweeptime] = HP_SpecAn_Resbandwidth_Sweeptime(resbandwidth, sweeptime, HP_SpecAn)
    [SpecAn_Centre, SpecAn_Span] = HP_SpecAn_Centre_Span(centre, span, HP_SpecAn)
    [SpecAn_track, SpecAn_Power] = HP_SpecAn_RF(tracking_gen, RF_power, HP_SpecAn)
    
    
    Arduino.write('0')
    val = Arduino.read()
    
    #this if statement determines if the correct .ino file is loaded onto the 
    #arduino, and loads the freerun.ino if neccesary
    if (val != 'EIT test program complete'):
        
        #the arduino has the wrong .ino file so we must delete the visa handle in 
        #in order to upload the correct program
        del Arduino
        Upload_Arduino('EIT_AOM')
        #once we start uploading the new script to the arduino, we need to wait 
        #12 seconds for it to complete
        time.sleep(12)
        
        #we now regenerate the handle and open the correct RF channels for the
        #spectrum analyser by starting the 'pulse sequence'
        Arduino = Initialise_Arduino(arduino_comport)
    
    for i in range (1,1000):
        #sets up registers for data reading
        HP_SpecAn.write("CLES; *SRE 4; ESNB 1")
        #triggers spectrum analyser for data reading
        HP_SpecAn_Trigger(trig_source, trig_type, trig_polarity, HP_SpecAn)

        #need to wait 100ms for spectrum analyser trigger to set before
        #we can start the pulse program, otherwise spectrum analyser gets
        #stuck waiting for trigger because it missed it
        time.sleep(0.1)
     
        Arduino.write('0')
        print Arduino.read()
        
        #Waits for Spectrum Analyser to finish Data sweep
        HP_SpecAn.wait_for_srq()

        x_axis_data = HP_SpecAn.ask_for_values("OUTPSWPRM?",double | big_endian)
        y_axis_data = HP_SpecAn.ask_for_values("OUTPDTRC?",double | big_endian)


        display_start = 30
        display_end = 790
        data_plot_window(x_axis_data,y_axis_data, 0, 0, 0, display_start, display_end)
    
    #turns off the RF and returns the spectrum analyser back to normal state.
    HP_SpecAn_Trigger('INT', 'CONT', trig_polarity, HP_SpecAn)
        
    
    
#


def free_run():
    
    #the following sets python to interactive mode so that we can see the spectrum analyser
    #output as a GUI
    pylab.ion()
    
    
    #here we generate a handle for the spectrum analyser, turn on the RF and
    #set it to trigger internally
    global HP_SpecAn_Bool
    global HP_SpecAn

    global Burleigh_WM_Bool
    global Burleigh_WM
    
    [HP_SpecAn, HP_SpecAn_Bool] = Initialise_HP_SpecAn()
    [Burleigh_WM, Burleigh_WM_Bool] = Initialise_Burleigh_WM()
    
    
    HP_SpecAn_Trigger('INT', 'CONT', trig_polarity, HP_SpecAn)
    
    [SpecAn_BW, SpecAn_Sweeptime] = HP_SpecAn_Resbandwidth_Sweeptime(resbandwidth, sweeptime, HP_SpecAn)
    [SpecAn_Centre, SpecAn_Span] = HP_SpecAn_Centre_Span(centre, span, HP_SpecAn)
    [SpecAn_track, SpecAn_Power] = HP_SpecAn_RF(tracking_gen, RF_power, HP_SpecAn)
    
    #we generate an instrument handle for the arduino, so that we can see which
    #.ino it has loaded, and load the freerunning .ino if necessary
    Arduino = Initialise_Arduino(arduino_comport)
    Arduino.write('0')
    
    #we need to set the execution to interactive mode so that the when the 
    #spectrum is plotted, the windows does not block further code execution
    #(this is a quirk of matlibplot)
    pylab.ion()
    val = Arduino.read()
    print val
    #this if statement determines if the correct .ino file is loaded onto the 
    #arduino, and loads the freerun.ino if neccesary
    if (val == 'Spectrum Analyser is on Freerun'):
        #plotting function
        free_run_plot_window()
    else:
        
        #the arduino has the wrong .ino file so we must delete the visa handle in 
        #in order to upload the correct program
        del Arduino
        Upload_Arduino('arduino_freerun')
        #once we start uploading the new script to the arduino, we need to wait 
        #12 seconds for it to complete
        time.sleep(12)
        
        #we now regenerate the handle and open the correct RF channels for the
        #spectrum analyser by starting the 'pulse sequence'
        Arduino = Initialise_Arduino(arduino_comport)
        Arduino.write('0')    
        Arduino.read()
        
        #plotting function
        free_run_plot_window()
        
#


def data_plot_window(x_axis_data,y_axis_data, resistance, temp, filename, display_start, display_end):
    
    
    clf()

    plot(x_axis_data[display_start:display_end], y_axis_data[display_start:display_end])
    title(str(resistance) + 'K Ohm, ' + str(temp) + ' K', fontsize = 50)
    xlim([centre-span*(0.5 - (float(display_start)/800)), centre+span*((float(display_end)/800) - 0.5)])
    xlabel(filename, fontsize = 50)
    
    bexit = Button(axes([0.88, 0.91, 0.09, 0.07]), 'Quit', image=None, color=u'0.8', hovercolor=u'1')
    bexit.on_clicked(exit_button)
    pause(0.01)
#


def free_run_plot_window():
    

    global CB_state
    CB_state = False
    global get_axis_state
    get_axis_state = True
    #global wavelength
    #wavelength_bool = 0
    #location = "C:\Users\Milos\Desktop\\wavlengthdata.txt"
    #wavelengthfile = open(location, 'r')
    
    while True:

        freq = Burleigh_WM.ask_for_values("FETC:SCAL:FREQ?")
        frequency = freq[0]
        
        y_axis_data = HP_SpecAn.ask_for_values("OUTPDTRC?",double | big_endian)

        #we clear the figure before we plot, so that we dont replot over the 
        #old data        
        clf()

        plot([(centre-span/2)+i*(span/801) for i in range(801)],y_axis_data)
        title(str(frequency) + ' THz', fontsize = 100)
 
        if (CB_state == True):
            if (get_axis_state == True):
                axis_matrix = axis()
                get_axis_state = False
                if (axis_matrix[3] < 0):
                    axis([centre-span/2, centre+span/2, axis_matrix[2]*1.1, axis_matrix[3]*0.8])
                else:
                    axis([centre-span/2, centre+span/2, axis_matrix[2]*1.1, axis_matrix[3]*1.2])
  
        #round the wavelength number and plot it as a button
       
        #bwavelength = Button(axes([0.3, 0.91, 0.25, 0.09]), str(frequency) + ' THz'
        
        #this generates an exit button to quit the scan and return the instrument
        #handle to prevent the spectrum analyser and OSA from freezing
        bexit = Button(axes([0.9, 0.91, 0.09, 0.07]), 'Quit', image=None, color=u'0.8', hovercolor=u'1')
        bexit.on_clicked(exit_button)
      
        #this check box fixes the Y scale so that it doesnt fluctuate (makes looking at the data
        #a bit disorienting otherwise
        CB_fix_axis = CheckButtons(axes([0.9, 0.8, 0.09, 0.07]), ('fix Axis',),(CB_state,))
        CB_fix_axis.on_clicked(fix_axis)
        
        #this pause statement is necessary as otherwise the plotting window
        #freezes. this seems to be a bug with the current version of python/matplotlib
        pause(0.01)
#


def exit_button(arg):
    
    
    print 'exiting'

    #closes the visa session to the spectrum analyser if it is being used
    if (HP_SpecAn_Bool == 1):
        HP_SpecAn_Trigger('INT', 'CONT', trig_polarity, HP_SpecAn)
        HP_SpecAn.close()
        print '-disconnected from Spectrum Analyser'
        
    if (Agilent_OSA_Bool == 1):
        Agilent_OSA.close()
        print '-disconnected from OSA'
        
    #if (Rigol_DMM_Bool == 1):
    #    Rigol_DMM.close()
    #    print '-disconnected from DMM'
        
    if (WindfreakV2_Bool == 1):
        WindfreakV2.close()
        print '-disconnected from Windfreak'
    
    quit()


    

#


def fix_axis(axis_state):
    global get_axis_state
    global CB_state
    
    CB_state = not CB_state
    if (CB_state == True):
        cla()
    else:    
        get_axis_state = True

#


def get_temperature():
    
    
    
    
    [Rigol_DMM, Rigol_DMM_Bool] = Initialise_DMM()
    [resistance, temp] = Rigol_DMM_Measure_Resistance(Rigol_DMM)
    print resistance
    del Rigol_DMM
#


def get_wavelength():
    
    
    [Agilent_OSA, Agilent_OSA_Bool] = Initialise_OSA()
    print OSA_measure_wavelength(Agilent_OSA)
    del Agilent_OSA
#


def run_arduino():
    
    
    Arduino = Initialise_Arduino("COM10")
    Arduino.write('0')
    print Arduino.read()


#


#need to execute code as a try/except statement, otherwise if you break the code manually,
#visa seems to not return the instrument handles. This causes the GPIB card to freeze,
#so the PC must be restarted before you can run the program again...annoying




try: 

#############CHOOSE ONE OF THE FOLLOWING TO EXECUTE###############
    #main_loop()
    test()
    #loop_test()
    #free_run()
    #run_arduino()
    #get_temperature()
    #get_wavelength()
except KeyboardInterrupt:
    print 'failed'
    del HP_SpecAn




