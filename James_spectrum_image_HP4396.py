import sys
import numpy as np
from ctypes import *
import time
import matplotlib.pyplot as plt
import matplotlib.widgets as widget
from visa import *
from struct import *
from HP_Spectrum_Analyser import *
from Arduino_Pulseblaster_SpecAn_Trench import *
from Rigol_DMM import *
## from Burleigh_Wavemeter import *
from Stanford_FG import *
import numpy as np
import binascii
import os
import pylab
import pulse_blaster as pb

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
global ThreeGHz_SpecAn_Bool
global Burleigh_WM_Bool
global Rigol_DMM_Bool

HP_SpecAn_Bool = 0
ThreeGHz_SpecAn_Bool = 0
Rigol_DMM_Bool = 0
Burleigh_WM_Bool = 0


laser_wavelength = 'Not Queried'
SpecAn_BW = 'Not Queried'
SpecAn_Centre = 'Not Queried'
SpecAn_Span = 'Not Queried'
SpecAn_Sweeptime = 'Not Queried'
SpecAn_Power = 'Not Queried'



arduino_comport = 'COM10'

#----------HP 4396A Spectrum/Network Analyser Global Variables-----------------#

#IMPORTANT: there is a 16.3 ms delay between triggering the Spectrum Analyser
#and beginning a scan. Hence the spectrum analyser should be triggered ahead
#of RF to achieve the desired delay


#input whether to turn on tracking generator and specify the RF power in dBm
tracking_gen = 'ON'  #accepts 'ON' or 'OFF'



#input the sweeptime and resolution bandwidth, otherwise set to AUTO


def save_trace(HP_SpecAn, filename = 'HP4396_trace'):
    filepath = "C:\Users\Milos\Desktop\James\\" + filename +'.txt'
    
    try:
        os.remove(filename)
    except OSError:
        pass
    file = open(filepath,'w')
    
    y_axis_data = HP_SpecAn.query_binary_values("OUTPDTRC?",datatype= u'd', is_big_endian = True)
    x_axis_data = HP_SpecAn.query_binary_values("OUTPSWPRM?",datatype= u'd',is_big_endian = True)
    
    data = np.vstack([x_axis_data, y_axis_data]).T
    np.savetxt(file, data, fmt='%.10e')



#
def save_data(filename, folder_name,  spec_data):
    
    
    
    day = time.strftime("%d")
    month = time.strftime("%m")
    year = time.strftime("%Y")
    hour = time.strftime("%H")
    minute = time.strftime("%M")
    second = time.strftime("%S")
    
    date_string = day + "_" + month + "_" + year
    time_string = hour + "Hrs " + minute + "Mins " + second + "Secs"
    
    filepathA = "C:\Users\Milos\Desktop\James\\" + date_string

    if not os.path.exists(filepathA):
        os.mkdir(filepathA)
        
    filepathB = "C:\Users\Milos\Desktop\James\\" + date_string + "\\" + folder_name

    if not os.path.exists(filepathB):
        os.mkdir(filepathB)
        

        


  
    
    for i in range(len(spec_data)):
        OutputFile.write(str(spec_data[i]) + ",  " 
        + str(wavelength_values[i])+ ",  " + str(frequency_values[i]) + "\n")
    
#     


#
def free_run(compensated):
    
    
    
    #here we generate a handle for the spectrum analyser, turn on the RF and
    #set it to trigger internally
    global HP_SpecAn_Bool
    global HP_SpecAn

    global Burleigh_WM_Bool
    global Burleigh_WM
    
    [HP_SpecAn, HP_SpecAn_Bool] = Initialise_HP_SpecAn()
    [Burleigh_WM, Burleigh_WM_Bool] = Initialise_Burleigh_WM()
    
    
    HP_SpecAn_Trigger('INT', 'CONT', 'POS', HP_SpecAn)
    
    [SpecAn_BW, SpecAn_Sweeptime] = HP_SpecAn_Resbandwidth_Sweeptime(resbandwidth, sweeptime, HP_SpecAn)
    [SpecAn_Centre, SpecAn_Span] = HP_SpecAn_Centre_Span(centre, span, HP_SpecAn)
    [SpecAn_track, SpecAn_Power] = HP_SpecAn_RF(tracking_gen, RF_power, HP_SpecAn)
    

    #we need to set the execution to interactive mode so that the when the 
    #spectrum is plotted, the windows does not block further code execution
    #(this is a quirk of matlibplot)
    pylab.ion()
    free_run_plot_window(compensated)
        
#


#
def save_offset(avg_num):
    
    
    
    
    [HP_SpecAn, HP_SpecAn_Bool] = Initialise_HP_SpecAn()
    
    offset_array = np.zeros((avg_num,801),dtype=float)
    [SpecAn_track, SpecAn_Power] = HP_SpecAn_RF(tracking_gen, RF_power, HP_SpecAn)
    time.sleep(0.1)
    #now we collect the data trace
    for i in range(avg_num):
        
        offset_data_temp = HP_SpecAn.query_binary_values("OUTPDTRC?",datatype= u'd', is_big_endian = True)
        offset_array[i,:] = offset_data_temp[:]
        time.sleep(0.2)
    avg_offset_data = np.average(offset_array,0)
    np.savetxt("C:\\Users\\Milos\Desktop\\Er_Experiment_Interface_Code\\amplitude_offset.csv", avg_offset_data,fmt='%.10e',delimiter=",")
#


#
def free_run_plot_window(compensated):
    

    global CB_state
    CB_state = False
    global get_axis_state
    get_axis_state = True
    
    
    
    #adjust the plotted data to compensate for modulator RF and InGaAs detector response
    if compensated == 'Y':
        amplitude_offset = np.loadtxt("C:\\Users\\Milos\Desktop\\Er_Experiment_Interface_Code\\amplitude_offset.csv",delimiter=",")
    
    

    
    while True:

        #freq = Burleigh_WM.query_ascii_values("FETC:SCAL:FREQ?")
        #frequency = freq[0]
        
        y_axis_data = HP_SpecAn.query_binary_values("OUTPDTRC?",datatype= u'd', is_big_endian = True)
        x_axis_data = HP_SpecAn.query_binary_values("OUTPSWPRM?",datatype= u'd',is_big_endian = True)
        y_axis_data = y_axis_data[0::2]

        
        if compensated == 'Y':
            compensated_data = np.divide(y_axis_data,amplitude_offset)
            #we clear the figure before we plot, so that we dont replot over the 
            #old data 
            plt.clf()
            plt.plot(x_axis_data,compensated_data)
        else:
            #we clear the figure before we plot, so that we dont replot over the 
            #old data 
            plt.clf()
            plt.plot(x_axis_data,y_axis_data)
       

        #plt.title(str(frequency) + ' THz', fontsize = 100)

      
        if (CB_state == True):
     
            if (get_axis_state == True):
                axis_matrix = plt.axis()
                get_axis_state = False
            if (axis_matrix[3] < 0):
                plt.axis([centre-span/2, centre+span/2, axis_matrix[2]*1.05, axis_matrix[3]*0.9])
            else:
                plt.axis([centre-span/2, centre+span/2, axis_matrix[2]*0.95, axis_matrix[3]*1.02])
  
        #round the wavelength number and plot it as a button
       
        #bwavelength = Button(axes([0.3, 0.91, 0.25, 0.09]), str(frequency) + ' THz'
        
        #this generates an exit button to quit the scan and return the instrument
        #handle to prevent the spectrum analyser and OSA from freezing
        bexit = widget.Button(plt.axes([0.9, 0.91, 0.09, 0.07]), 'Quit', image=None, color=u'0.8', hovercolor=u'1')
        bexit.on_clicked(exit_button)
      
        #this check box fixes the Y scale so that it doesnt fluctuate (makes looking at the data
        #a bit disorienting otherwise
        CB_fix_axis = CheckButtons(plt.axes([0.9, 0.8, 0.09, 0.07]), ('fix Axis',),(CB_state,))
        CB_fix_axis.on_clicked(fix_axis)
        
        #this pause statement is necessary as otherwise the plotting window
        #freezes. this seems to be a bug with the current version of python/matplotlib
        plt.pause(0.01)
#


#
def data_plot_window(x_axis_data,y_axis_data, display_start, display_end):
    
    
    plt.clf()

    plt.plot(x_axis_data[display_start:display_end], y_axis_data[display_start:display_end])
    plt.xlim([centre-span*(0.5 - (float(display_start)/200)), centre+span*((float(display_end)/200) - 0.5)])
    #plt.ylim([0.4, 1])
    
    bexit = widget.Button(plt.axes([0.88, 0.91, 0.09, 0.07]), 'Quit', image=None, color=u'0.8', hovercolor=u'1')
    bexit.on_clicked(exit_button)
    plt.show()

#


#
def exit_button(arg):
    
    
    print 'exiting'
    
 
    
    #closes the visa session to the spectrum analyser if it is being used
    if (HP_SpecAn_Bool == 1):
        HP_SpecAn_Trigger('INT', 'CONT', 'POS', HP_SpecAn)
       # HP_SpecAn_RF('OFF', RF_power, HP_SpecAn)
        HP_SpecAn.close()
        print '-disconnected from Spectrum Analyser'
        
    if (ThreeGHz_SpecAn_Bool == 1):
        ThreeGHz_SpecAn.close()
        print '-disconnected from 3Ghz Spectrum Analyser'
        
    #if (Rigol_DMM_Bool == 1):
    #    Rigol_DMM.close()
    #    print '-disconnected from DMM'
        
 
    quit()

#


#
def fix_axis(axis_state):
    global get_axis_state
    global CB_state
    CB_state = not CB_state
    if (CB_state == True):
        plt.cla()
    else:    
        get_axis_state = True

#


#
def burn_scan_image(burn_centre,burn_span,burn_power,direction):
    
    global HP_SpecAn
    
    #initialise the equiptment
    Arduino = Initialise_Arduino(arduino_comport)
    [Burleigh_WM, Burleigh_WM_bool] = Initialise_Burleigh_WM()
    [HP_SpecAn, HP_SpecAn_Bool] = Initialise_HP_SpecAn()
    
    #set the spectrum analyser sweeping to burn out a trench
    HP_SpecAn_Trigger('INT', 'CONT', trig_polarity, HP_SpecAn)
    [SpecAn_track, SpecAn_Power] = HP_SpecAn_RF('ON', burn_power, HP_SpecAn)
    [SpecAn_Centre, SpecAn_Span] = HP_SpecAn_Centre_Span(burn_centre, burn_span, HP_SpecAn)
    [SpecAn_BW, SpecAn_Sweeptime] = HP_SpecAn_Resbandwidth_Sweeptime('AUTO', 300*ms, HP_SpecAn)

    #get the laser wavelength
    Burleigh_WM.write("FETC:SCAL:WAV?")
    laser_wavelength = np.float(Burleigh_WM.read())
    
    #now that the program has started, let the spectrum analyser scan out a trench for time.sleep(x-1)
    #seconds.
    #in the end, whether the light is on will depend on the AOM shutter
    #wait a bit for the command to go through, before we start the arduino pulse program
    time.sleep(0.1)
 
    Arduino.write('0')
    print Arduino.read() 
    

    time.sleep(30)

    #sends necessary pre-data collection settings to the Spectrum Analyser

    [SpecAn_BW, SpecAn_Sweeptime] = HP_SpecAn_Resbandwidth_Sweeptime(3*MHz, sweeptime, HP_SpecAn)
    [SpecAn_Centre, SpecAn_Span] = HP_SpecAn_Centre_Span(centre, span, HP_SpecAn)
    [SpecAn_track, SpecAn_Power] = HP_SpecAn_RF(tracking_gen, RF_power, HP_SpecAn)
    [SpecAn_Centre, SpecAn_Span] = HP_SpecAn_Centre_Span(centre, span, HP_SpecAn)
    
    #sets up registers for data reading
    HP_SpecAn.write("CLES; *SRE 4; ESNB 1")
    #triggers spectrum analyser for data reading
    HP_SpecAn_Trigger(trig_source, trig_type, trig_polarity, HP_SpecAn)

    
    #Waits for Spectrum Analyser to finish Data sweep
    HP_SpecAn.wait_for_srq(timeout = 3050000)
    
    
    #generate the array to compensate for the RF and Detector response
    amplitude_offset = np.loadtxt("C:\\Users\\Milos\Desktop\\Er_Experiment_Interface_Code\\amplitude_offset.csv",delimiter=",")
    
    x_axis_data = np.array(HP_SpecAn.query_binary_values("OUTPSWPRM?",datatype= u'd',is_big_endian = True))
    y_axis_data = np.array(HP_SpecAn.query_binary_values("OUTPDTRC?",datatype= u'd',is_big_endian = True))
    
    #divide by offset to compensate
    y_axis_data = np.divide(y_axis_data, amplitude_offset)
    
    #speed of light
    c = 299792453
    
    #generate absolute wavelength and frequency information based on direction of scan
    if direction == 'pos':
        wavelength_values = x_axis_data*((laser_wavelength**2)/(c*10**9))+laser_wavelength
       
        frequency_values = -x_axis_data + (c*10**9)/laser_wavelength
    else:
        wavelength_values = -x_axis_data*((laser_wavelength**2)/(c*10**9))+laser_wavelength
        frequency_values = x_axis_data + (c*10**9)/laser_wavelength
    
    filename =  "2.0 torr, 3000 seconds"

    save_data(filename, folder_name,  laser_wavelength,
    y_axis_data, wavelength_values, frequency_values)
            
            
    display_start = 1
    display_end = 800
    data_plot_window(x_axis_data,y_axis_data, display_start, display_end)
    
    
    #turns off the RF and returns the spectrum analyser back to normal state.
    HP_SpecAn_Trigger('INT', 'CONT', trig_polarity, HP_SpecAn)
    [SpecAn_track, SpecAn_Power] = HP_SpecAn_RF('OFF', burn_power, HP_SpecAn)
#


#
def burn_scan_image_VCO(sweep_array,direction):
    
    global HP_SpecAn
    global HP_SpecAn_Bool
    global Stanford_Bool
    global Stanford_FG

    #initialise the equiptment
    Arduino = Initialise_Arduino(arduino_comport)
    [Burleigh_WM, Burleigh_WM_bool] = Initialise_Burleigh_WM()
    [HP_SpecAn, HP_SpecAn_Bool] = Initialise_HP_SpecAn()
    [Stanford_FG, Stanford_Bool] = Initialise_Stanford_FG()
    
    #get the laser wavelength
    Burleigh_WM.write("FETC:SCAL:WAV?")
    laser_wavelength = np.float(Burleigh_WM.read())
    #generate and upload the burn sweep to the Stanford and VCO
    [num_array, waveform_length] = VCO_Sweep(sweep_array, Stanford_FG, Stanford_Bool, HP_SpecAn, HP_SpecAn_Bool)
    Upload_to_Stanford_FG(num_array,waveform_length, Stanford_FG)
    
 
    Arduino.write('0')
    print Arduino.read() 
    
    
    #wait some time for the arduino to start the pulse program before setting trigger on SpecAn
    time.sleep(1)

    [SpecAn_BW, SpecAn_Sweeptime] = HP_SpecAn_Resbandwidth_Sweeptime(resbandwidth, sweeptime, HP_SpecAn)
    [SpecAn_Centre, SpecAn_Span] = HP_SpecAn_Centre_Span(centre, span, HP_SpecAn)
    [SpecAn_track, SpecAn_Power] = HP_SpecAn_RF(tracking_gen, RF_power, HP_SpecAn)
    [SpecAn_Centre, SpecAn_Span] = HP_SpecAn_Centre_Span(centre, span, HP_SpecAn)
    
    #sets up registers for data reading
    HP_SpecAn.write("CLES; *SRE 4; ESNB 1")
    #triggers spectrum analyser for data reading
    HP_SpecAn_Trigger(trig_source, trig_type, trig_polarity, HP_SpecAn)

    
    #Waits for Spectrum Analyser to finish Data sweep
    HP_SpecAn.wait_for_srq(timeout = 30000)

    
    
    #generate the array to compensate for the RF and Detector response
    
    #collect trace data off spectrum analyser
    x_axis_data = np.array(HP_SpecAn.query_binary_values("OUTPSWPRM?",datatype= u'd',is_big_endian = True))
    y_axis_data = np.array(HP_SpecAn.query_binary_values("OUTPDTRC?",datatype= u'd',is_big_endian = True))
    y_axis_data = y_axis_data[0::2]   

    #speed of light
    c = 299792453
    
    #generate absolute wavelength and frequency information based on direction of scan
    if direction == 'pos':
        wavelength_values = x_axis_data*((laser_wavelength**2)/(c*10**9))+laser_wavelength
       
        frequency_values = -x_axis_data + (c*10**9)/laser_wavelength
    else:
        wavelength_values = -x_axis_data*((laser_wavelength**2)/(c*10**9))+laser_wavelength
        frequency_values = x_axis_data + (c*10**9)/laser_wavelength
    
    filename =  "200 ms sweep time, 10 second burn, run 1"

    save_data(filename, folder_name,  laser_wavelength,
    y_axis_data, wavelength_values, frequency_values)
    
    #turns off the RF and returns the spectrum analyser back to normal state.
    HP_SpecAn_Trigger('INT', 'CONT', trig_polarity, HP_SpecAn)
    [SpecAn_track, SpecAn_Power] = HP_SpecAn_RF('OFF', RF_power, HP_SpecAn)

            
    display_start = 1
    display_end = 200
    data_plot_window(x_axis_data,y_axis_data, display_start, display_end)
    
    

#


#
def spectrum_image(avg_num,direction):
    
    
    pylab.ion()
    
    [HP_SpecAn, HP_SpecAn_Bool] = Initialise_HP_SpecAn()

    
    #set the spectrum analyser scanning
    HP_SpecAn_Trigger('INT', 'CONT', 'POS', HP_SpecAn)
    
    [SpecAn_BW, SpecAn_Sweeptime] = HP_SpecAn_Resbandwidth_Sweeptime(resbandwidth, sweeptime, HP_SpecAn)
    [SpecAn_Centre, SpecAn_Span] = HP_SpecAn_Centre_Span(centre, span, HP_SpecAn)
    [SpecAn_track, SpecAn_Power] = HP_SpecAn_RF(tracking_gen, RF_power, HP_SpecAn)
    
    #need initial x_axis measurements to generate output array
    x_axis_data = np.array(HP_SpecAn.query_binary_values("OUTPSWPRM?",datatype= u'd',is_big_endian = True),dtype=float)
    
    #load in the offset from InGaAs detector and Modulator response
    amplitude_offset = np.loadtxt("C:\\Users\\Milos\Desktop\\Er_Experiment_Interface_Code\\amplitude_offset.csv",delimiter=",")
    
    compensated_array = np.zeros((avg_num,801),dtype=float)
    

   
    #convert x axis from frequency to wavelength
    
    if direction == 'pos':
        wavelength_values = x_axis_data*((laser_wavelength**2)/(c*10**9))+laser_wavelength
       
        frequency_values = -x_axis_data + (c*10**9)/laser_wavelength
    else:
        wavelength_values = -x_axis_data*((laser_wavelength**2)/(c*10**9))+laser_wavelength
        frequency_values = x_axis_data + (c*10**9)/laser_wavelength
    

    
    #now we collect the data trace
    for i in range(avg_num):
        plt.clf()
        spec_data_temp = HP_SpecAn.query_binary_values("OUTPDTRC?",datatype= u'd', is_big_endian = True)
        
        compensated_data = np.divide(spec_data_temp,amplitude_offset)
        
        compensated_array[i,:] = compensated_data[:]
        plt.plot(wavelength_values,compensated_data)
        plt.pause(0.01)
   
   
   
    
    #average the above runs into one array
    avg_spec_data = np.average(compensated_array,0)
    
    #print avg_spec_data
    
    plt.clf()
    pylab.ioff()
    
    foldername = '2 torr equilibrium'
    filename = str(laser_wavelength) + ' nm'
    
    
    if direction == 'pos':
        
        save_data(filename, foldername, laser_wavelength, avg_spec_data, wavelength_values, frequency_values)
        plt.plot(wavelength_values-1538,avg_spec_data)
        plt.xlim(wavelength_values[1]-1538,wavelength_values[-1]-1538)
        plt.show()

    else:
        
        save_data(filename, foldername, laser_wavelength, np.flipud(avg_spec_data), 
        np.flipud(wavelength_values), np.flipud(frequency_values))
        plt.plot(np.flipud(wavelength_values)-1538,np.flipud(avg_spec_data))
        plt.xlim(wavelength_values[-1]-1538,wavelength_values[1]-1538)
        plt.show()

#



def run_arduino():
 
    Arduino = Initialise_Arduino(arduino_comport)
    
    time.sleep(1)
    Arduino.write('0')
    print Arduino.read()


if __name__ == "__main__":
    [HP_SpecAn, HP_Bool] = Initialise_HP_SpecAn()
    save_trace(HP_SpecAn, 'Noise')
    
##     pb.Sequence([(['ch3','ch5'], 2*us),(['ch5'], 90*us),(['ch2','ch5'], 2*us), (['ch5'], 10*us)], loop=True)











## #
## #need to execute code as a try/except statement, otherwise if you break the code manually,
## #visa seems to not return the instrument handles. This causes the GPIB card to freeze,
## #so the PC must be restarted before you can run the program again...annoying




## #input the spectrum span and centre frequency in Hz
## span = 1.79*GHz
## centre = 900*MHz

## #span = 600*GHz
## #centre = 550*MHz


## RF_power = -10 #in dBm
## sweeptime =  'AUTO' #in seconds, otherwise set to 'AUTO'
## resbandwidth = 'AUTO' # in Hz, otherwise set to 'AUTO'

## folder_name = "spin polarisation temperature dependance 7 Tesla"

## #inputs triggering options, see "Intro to Spec An commands"
## trig_source = "EXT"
## trig_type = "SING"
## trig_polarity = "POS"

## #input stanford parameters for VCO burn (1.726 to 3.897 GHz). each section corresponds to one sweep section
## sweep_array = np.array([[1.9*GHz, 2.6*GHz, 200*ms]])


## try: 

##    

###########CHOOSE ONE OF THE FOLLOWING TO EXECUTE###############

##     
##     free_run('N') #choose 'Y' or 'N' to compensate  the plotted data 
##     
##     #for modulator RF and InGaAs detector response 
##     #save_offset(20)  #number of background runs to average so to make clean background trace
##     #spectrum_image(10,'pos')
##     
##     #burn a deep trench then scan image, 
##     #burn_scan_image(500*MHz, 600*MHz, 20, 'pos')  #burn_centre, burn_span, burn_power, direction
##     #burn_scan_image_VCO(sweep_array, 'pos')  
##     
##     #run_arduino()
##     
## except KeyboardInterrupt:
##     print 'failed'
##     del HP_SpecAn




