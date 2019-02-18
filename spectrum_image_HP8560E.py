import sys
from ctypes import *
import time
import matplotlib.pyplot as plt
import matplotlib.widgets as widget
from visa import *
from struct import *
from Arduino_Pulseblaster_SpecAn_Trench import *
from Rigol_DMM import *
from Burleigh_Wavemeter import *
from HP8560E_Spectrum_Analyser import *
#from Stanford_FG import *
from Agilent_OSA import *

import pulse_blaster as pb
import numpy as np
import binascii
import os
import pylab
import math

from matplotlib.widgets import CheckButtons


#some usefull constants
Hz = 1
kHz = 10**3
MHz = 10**6
GHz = 10**9

ns = 10**-9
us = 10**-6;
ms = 10**-3;
s = 1;

#the following booleans determine if the the corresponding equiptment is being used
#they return a 1 when the equiptment is initialised, otherwise they return 0.
#this is neccesary so that you can close the correct visa sessions when you 
#want to quit the program


SpecAn_Bool = 0
Stanford_Bool = 0
Rigol_DMM_Bool = 0
Burleigh_WM_Bool = 0


laser_wavelength = 'Not Queried'
SpecAn_BW = 'Not Queried'
SpecAn_Centre = 'Not Queried'
SpecAn_Span = 'Not Queried'
SpecAn_Sweeptime = 'Not Queried'
SpecAn_Power = 'Not Queried'


arduino_comport = 'COM10'
[SpecAn, SpecAn_Bool] = Initialise_HP8560E_SpecAn()



#
def save_data(filename, folder_name,  laser_wavelength,
    spec_data, wavelength_values, frequency_values):
    
    
    
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
        
    filepathB = "C:\Users\Milos\Desktop\EIT Data\\" + date_string + "\\" + folder_name

    if not os.path.exists(filepathB):
        os.mkdir(filepathB)
        

        
    location = filepathB + "\\" + filename + ".txt"
    OutputFile = open(location, 'w')
    OutputFile.write("The Date is: " + date_string + "\n")
    OutputFile.write("The Time is: " + time_string + "\n")
    OutputFile.write("The laser wavelength is: " + str(laser_wavelength) +  " nm \n")
    OutputFile.write(str(laser_wavelength)+"\n")

  
    
    for i in range(len(spec_data)):
        OutputFile.write(str(spec_data[i]) + ",  " 
        + str(wavelength_values[i])+ ",  " + str(frequency_values[i]) + "\n")
    
#     


#
def free_run(compensated):
    
    
    
    #here we generate a handle for the spectrum analyser, turn on the RF and
    #set it to trigger internally
    global SpecAn_Bool
    global SpecAn
    
    SpecAn.write("SP?")
    span = SpecAn.read()
    SpecAn.write("CF?")
    centre = SpecAn.read()
    SpecAn.write("RB?")
    resbandwidth = SpecAn.read() 
    SpecAn.write("SRCPWR?")
    RF_power = SpecAn.read()
    SpecAn.write("ST?")
    sweeptime =  SpecAn.read() 
    
    print "centre is: " + centre

    #global Burleigh_WM_Bool
    #global Burleigh_WM
    
    [SpecAn, SpecAn_Bool] = Initialise_HP8560E_SpecAn()
    #[Burleigh_WM, Burleigh_WM_Bool] = Initialise_Burleigh_WM()
 
    
    [SpecAn_BW, SpecAn_Sweeptime] = HP8560E_SpecAn_Resbandwidth_Sweeptime(resbandwidth, sweeptime, SpecAn)
    [SpecAn_Centre, SpecAn_Span] = HP8560E_SpecAn_Centre_Span(centre, span, SpecAn)
    [SpecAn_track, SpecAn_Power] = HP8560E_SpecAn_RF(tracking_gen, RF_power, SpecAn)
    
    
    
    #send all the pulse blaster channels low so that we get the Tracking Generator RF
    #pb.Sequence([([], 1*us),],loop=False)

    
    
    #we need to set the execution to interactive mode so that the when the 
    #spectrum is plotted, the windows does not block further code execution
    #(this is a quirk of matlibplot)
    pylab.ion()
    free_run_plot_window(compensated, centre, span)
    #noise_floor_plot_window(compensated, centre, span)
    

#


#
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
    


def save_offset(avg_num, full_span = 'N'):
    
    #Allows for two offsets, one dedicated as a fully span off set and the other
    #for various spans/frequencies
    if full_span == 'N':
        save_file = "C:\\Users\\Milos\Desktop\\Er_Experiment_Interface_Code\\amplitude_offset.csv"
    elif full_span == 'Y':
        save_file = "C:\\Users\\Milos\Desktop\\Er_Experiment_Interface_Code\\amplitude_offset_full.csv"
    else:
        save_file = full_span
    
    [SpecAn, SpecAn_Bool] = Initialise_HP8560E_SpecAn()
    SpecAn.write("SRCPWR?")
    SpecAn_Power = SpecAn.read()
    print "Power is: " + str(SpecAn_Power)
    sweep = float(SpecAn.query('ST?'))
    
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
##     [SpecAn_track, SpecAn_Power] = HP8560E_SpecAn_RF(tracking_gen, RF_power, SpecAn)
    #now we collect the data trace
    for i in range(avg_num):
        
        pb.Sequence([(['ch2','ch5','ch4'], 1*ms)], loop=False)
        sleep(sweep+0.05)
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
def noise_floor_plot_window(compensated, centre, span):
    
    

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
        
        SpecAn.write("TRA?")
        
        binary_string = SpecAn.read_raw()
        hex_string = binascii.b2a_hex(binary_string)
        y_axis_data = np.zeros(601)
 
        
        for i in range (601):
            
            y_axis_data[i] = int('0x' + hex_string[i*4: i*4+4], 0)
            
        x_axis_data = np.arange(centre-span/2, centre+span/2, span/601)
        #print y_axis_data
        if compensated == 'Y':
            compensated_data = np.subtract(y_axis_data,amplitude_offset)
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
                #plt.axis([centre-span/2, centre+span/2, axis_matrix[2]*1.05, axis_matrix[3]*0.9])
                plt.axis([centre-span/2, centre+span/2, axis_matrix[2]*1.0001, axis_matrix[3]*0.9])
            else:
                #plt.axis([centre-span/2, centre+span/2, axis_matrix[2]*0.95, axis_matrix[3]*1.02])
                plt.axis([centre-span/2, centre+span/2, axis_matrix[2]*0.9995, axis_matrix[3]*1.0001])
  
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

def free_run_plot_window_new(compensated, centre = 1.45*GHz, span = 2.9*GHz, full_span = 'N'):
    global CB_state
    CB_state = False
    global get_axis_state
    get_axis_state = True
    
    #Allows for two offsets, one dedicated as a fully span off set and the other
    #for various spans/frequencies
    if full_span == 'N':
        save_file = "C:\\Users\\Milos\Desktop\\Er_Experiment_Interface_Code\\amplitude_offset.csv"
    elif full_span == 'Y':
        save_file = "C:\\Users\\Milos\Desktop\\Er_Experiment_Interface_Code\\amplitude_offset_full.csv"   
    
    #adjust the plotted data to compensate for modulator RF and InGaAs detector response
    if compensated == 'Y':
        amplitude_offset = np.loadtxt(save_file,delimiter=",")
    #figure(0
    #Traces are made up of 601 points (x axis) with a value from 0 to 610
    #This can be converted into dB
    SpecAn.write('LG?')
    dB_div = float(SpecAn.read())
    entire_depth = 10*dB_div #how many dB in the entire display
    SpecAn.write('RL?') #Get the reference level
    ref_level = float(SpecAn.read())
    SpecAn.write('CF?')
    centre = float(SpecAn.read())
    SpecAn.write('SP?')
    span = float(SpecAn.read())
    
    lowest_point = ref_level - entire_depth 
    #To convert Y data to dB -> y_data*entire_depth/610 + lowest_point
    
    def get_data(bCompensated):
        #frequency = freq[0]
        SpecAn.write("TRA?")
        
        binary_string = SpecAn.read_raw()
        hex_string = binascii.b2a_hex(binary_string)
        y_axis_data = np.zeros(601)
 
        
        for i in range (601):
            
            y_axis_data[i] = int('0x' + hex_string[i*4: i*4+4], 0)
            
        x_axis_data = np.linspace(centre-span/2, centre+span/2, 601)
        y_axis_data = y_axis_data*entire_depth/610 + lowest_point #Convert to dB
        
        if bCompensated:
            y_axis_data = np.subtract(y_axis_data,amplitude_offset)
        
        return x_axis_data, y_axis_data
    
    def make_plot(xAx, yAx):
        if not plt.fignum_exists(__file__):
            fig=plt.figure(__file__);
        else:
            fig=plt.gcf();
        ax=plt.gca()
                
        line=ax.plot(xAx,yAx)[0]
        ax.set_xlabel('Frequency (Hz)')
        if compensated=='Y':
            ax.set_xticks(np.arange(min(xAx), max(xAx), 
                                 (max(xAx)-min(xAx))/(2.9*5)))
            ax.set_ylabel('Trace - background (dB)')
        else:
            ax.set_ylabel('Trace (dB)')
            
        def exit_clicked(event):
            flQuit[0]= True
        
        buttExit = widget.Button(plt.axes([0.9, 0.91, 0.09, 0.07]), 'Quit', image=None, color=u'0.8', hovercolor=u'1')
        buttExit.on_clicked(exit_clicked)
        
        def pause_clicked(event):
            flRun[0]= not flRun[0]
        #cButtPause = CheckButtons(plt.axes([0.9, 0.7, 0.09, 0.07]), ('pause',),(False,))[0]

        buttPause = widget.Button(plt.axes([0.9, 0.7, 0.09, 0.07]), 'Pause', image=None, color=u'0.8', hovercolor=u'1')
        buttPause.on_clicked(pause_clicked)
      
        #this check box fixes the Y scale so that it doesnt fluctuate (makes looking at the data
        #a bit disorienting otherwise
        buttFix = widget.Button(plt.axes([0.9, 0.8, 0.09, 0.07]), 'fix Axes')
        
        def fix_clicked(event):
            #xDat=line.get_xdata()
            #ax.set_xlim([xDat[0], xDat[-1]])
            #yDat=line.get_ydata()
            #ax.set_ylim([yDat[0], yDat[-1]])
            ax.autoscale(enable=True)
            #print('Currently {}'.format(val))
             
            
        buttFix.on_clicked(fix_clicked )
        #make_plot.buttons=[bexit, bPause, buttFix]
        return ax, line, buttExit, buttPause, buttFix
            
    xAx,yAx=get_data(True if compensated=='Y' else False)
    ax, line, buttExit, buttPause, buttFix =make_plot(xAx, yAx)
    flRun = [True]
    flQuit = [False]
    try: 
        while not flQuit[0]:
            if flRun[0]:
                xAx,yAx=get_data(True if compensated=='Y' else False)
                line.set_xdata(xAx);
                line.set_ydata(yAx)
            #freq = Burleigh_WM.query_ascii_values("FETC:SCAL:FREQ?")
       
            #print y_axis_data



       
            
            #plt.title(str(frequency) + ' THz', fontsize = 100)

            #round the wavelength number and plot it as a button
           
            #bwavelength = Button(axes([0.3, 0.91, 0.25, 0.09]), str(frequency) + ' THz'
            
            #this generates an exit button to quit the scan and return the instrument
            #handle to prevent the spectrum analyser and OSA from freezing

            #this pause statement is necessary as otherwise the plotting window
            #freezes. this seems to be a bug with the current version of python/matplotlib
            plt.pause(0.1)
    #
    finally:
        plt.close(ax.figure)

#
def free_run_plot_window_old(compensated, centre = 1.45*GHz, span = 2.9*GHz, full_span = 'N'):
    global CB_state
    CB_state = False
    global get_axis_state
    get_axis_state = True
    
    #Allows for two offsets, one dedicated as a fully span off set and the other
    #for various spans/frequencies
    if full_span == 'N':
        save_file = "C:\\Users\\Milos\Desktop\\Er_Experiment_Interface_Code\\amplitude_offset.csv"
    elif full_span == 'Y':
        save_file = "C:\\Users\\Milos\Desktop\\Er_Experiment_Interface_Code\\amplitude_offset_full.csv"   
    
    #adjust the plotted data to compensate for modulator RF and InGaAs detector response
    if compensated == 'Y':
        amplitude_offset = np.loadtxt(save_file,delimiter=",")
    
    #Traces are made up of 601 points (x axis) with a value from 0 to 610
    #This can be converted into dB
    SpecAn.write('LG?')
    dB_div = float(SpecAn.read())
    entire_depth = 10*dB_div #how many dB in the entire display
    SpecAn.write('RL?') #Get the reference level
    ref_level = float(SpecAn.read())
    
    lowest_point = ref_level - entire_depth 
    #To convert Y data to dB -> y_data*entire_depth/610 + lowest_point
    
    
    while True:

        #freq = Burleigh_WM.query_ascii_values("FETC:SCAL:FREQ?")
        #frequency = freq[0]
        
        SpecAn.write("TRA?")
        
        binary_string = SpecAn.read_raw()
        hex_string = binascii.b2a_hex(binary_string)
        y_axis_data = np.zeros(601)
 
        
        for i in range (601):
            
            y_axis_data[i] = int('0x' + hex_string[i*4: i*4+4], 0)
            
        x_axis_data = np.linspace(centre-span/2, centre+span/2, 601)
        y_axis_data = y_axis_data*entire_depth/610 + lowest_point #Convert to dB
        
        #print y_axis_data
        if compensated == 'Y':
            compensated_data = np.subtract(y_axis_data,amplitude_offset)
            #we clear the figure before we plot, so that we dont replot over the 
            #old data 
            plt.clf()
            plt.plot(x_axis_data,compensated_data)
            plt.xticks(np.arange(min(x_axis_data), max(x_axis_data), (max(x_axis_data)-min(x_axis_data))/(2.9*5)))
            plt.ylabel('Trace - background (dB)')
            plt.xlabel('Frequency (Hz)')
        else:
            #we clear the figure before we plot, so that we dont replot over the 
            #old data 
            plt.clf()
            plt.plot(x_axis_data,y_axis_data)
            plt.ylabel('Trace (dB)')
            plt.xlabel('Frequency (Hz)')
       
        
        #plt.title(str(frequency) + ' THz', fontsize = 100)

      
        if (CB_state == True):
     
            if (get_axis_state == True):
                axis_matrix = plt.axis()
                get_axis_state = False
            if (axis_matrix[3] < 0):
                #plt.axis([centre-span/2, centre+span/2, axis_matrix[2]*1.05, axis_matrix[3]*0.9])
                plt.axis([centre-span/2, centre+span/2, axis_matrix[2]*1.0001, axis_matrix[3]*0.9])
            else:
                #plt.axis([centre-span/2, centre+span/2, axis_matrix[2]*0.95, axis_matrix[3]*1.02])
                plt.axis([centre-span/2, centre+span/2, axis_matrix[2]*0.9995, axis_matrix[3]*1.0001])
  
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

free_run_plot_window=free_run_plot_window_new





#
def data_plot_window(x_axis_data,y_axis_data, display_start, display_end):
    
    
    plt.clf()

    plt.plot(x_axis_data[display_start:display_end], y_axis_data[display_start:display_end])
    plt.xlim([centre-span*(0.5 - (float(display_start)/601)), centre+span*((float(display_end)/601) - 0.5)])
    #plt.ylim([0.4, 1])
    
    bexit = widget.Button(plt.axes([0.88, 0.91, 0.09, 0.07]), 'Quit', image=None, color=u'0.8', hovercolor=u'1')
    bexit.on_clicked(exit_button)
    plt.show()

def free_run_plot_window_record_new(compensated, centre = 1.45*GHz, span = 0, full_span = 'N', record_length = 1*s):
    ''' Added by James, this is basically free_run_plot_window with the added feature of
    recording the data streamed. (modified by Morgan)'''
    

    global CB_state
    CB_state = False
    global get_axis_state
    get_axis_state = True
    
    #Allows for two offsets, one dedicated as a fully span off set and the other
    #for various spans/frequencies
    if full_span == 'N':
        save_file = "C:\\Users\\Milos\Desktop\\Er_Experiment_Interface_Code\\amplitude_offset.csv"
    elif full_span == 'Y':
        save_file = "C:\\Users\\Milos\Desktop\\Er_Experiment_Interface_Code\\amplitude_offset_full.csv"   
    
    #adjust the plotted data to compensate for modulator RF and InGaAs detector response
    if compensated == 'Y':
        amplitude_offset = np.loadtxt(save_file,delimiter=",")
    
    #Traces are made up of 601 points (x axis) with a value from 0 to 610
    #This can be converted into dB
    SpecAn.write('LG?')
    dB_div = float(SpecAn.read())
    entire_depth = 10*dB_div #how many dB in the entire display
    SpecAn.write('RL?') #Get the reference level
    ref_level = float(SpecAn.read())
    
    lowest_point = ref_level - entire_depth 
    #To convert Y data to dB -> y_data*entire_depth/610 + lowest_point
    
    
    SpecAn.write('SP ' + str(span))
    SpecAn.write('CF ' + str(centre))
    
    curTime=time.localtime()
    date_string=time.strftime('%Y-%m-%d', curTime)
    time_string=time.strftime('%H:%M.%S', curTime)

    #Data file set up
    data_file = "C:\Users\Milos\Desktop\James\\Time_series_data.csv" 
    #day = time.strftime("%d")
    #month = time.strftime("%m")
    #year = time.strftime("%Y")
    #hour = time.strftime("%H")
    #minute = time.strftime("%M")
    #second = time.strftime("%S")
    #
    #date_string = year + '-' + month + '-' + day
    #time_string = hour + ":" + minute + "." + second
    SpecAn.write('CF?')
    center = float(SpecAn.read())
    SpecAn.write('ST?')
    sweep = float(SpecAn.read())
    SpecAn.write('SP?')
    span = float(SpecAn.read())
    
    try:
        os.remove(data_file)
    except OSError:
        pass
    file = open(data_file,'w')
    if 0:
        # Less matlab-y is this:
        st_tmpl=("{date_string}\n"
        "{time_string}\n"
        "Time series recording of SpecAn. \n"
        "Center Freq: {center}\n"
        "Span: {span}\n"
        "Sweep time {sweep}\n"
        "Time length of recording: {record_length}\n"
        "\n")
        st=st_tmpl.format(date_string=date_string, time_string=time_string, 
            span=span, center=center, sweep=sweep, record_length=record_length)
    else:
        file.write(date_string + '\n')
        file.write(time_string + '\n')
        file.write('Time series recording of SpecAn. \n')
        file.write('Center Freq: ' + str(center) + '\n')
        file.write('Span: ' + str(span) + '\n')
        file.write('Sweep time: ' + str(sweep) + '\n')
        file.write('Time length of recording: ' + str(record_length) + '\n \n')
    
    #Number of loops needed to get required data
    loops = math.ceil(record_length/sweep) + 1
    loop_count = 0
    recorded_data = np.zeros((loops,601))
    
    while True:
        loop_count += 1
        #freq = Burleigh_WM.query_ascii_values("FETC:SCAL:FREQ?")
        #frequency = freq[0]
        
        SpecAn.write("TRA?")
        
        binary_string = SpecAn.read_raw()
        hex_string = binascii.b2a_hex(binary_string)
        y_axis_data = np.zeros(601)
 
        
        for i in range (601):
            
            y_axis_data[i] = int('0x' + hex_string[i*4: i*4+4], 0)
            
        x_axis_data = np.linspace(centre-span/2, centre+span/2, 601)
        y_axis_data = y_axis_data*entire_depth/610 + lowest_point #Convert to dB
        
        if loop_count < loops:
            recorded_data[loop_count,:] = y_axis_data
        
        #print y_axis_data
        if compensated == 'Y':
            compensated_data = np.subtract(y_axis_data,amplitude_offset)
            #we clear the figure before we plot, so that we dont replot over the 
            #old data 
            plt.clf()

            plt.plot(x_axis_data,compensated_data)
            plt.xticks(np.arange(min(x_axis_data), max(x_axis_data), (max(x_axis_data)-min(x_axis_data))/(2.9*5)))
            plt.ylabel('Trace - background (dB)')
            plt.xlabel('Frequency (Hz)')
        else:
            #we clear the figure before we plot, so that we dont replot over the 
            #old data 
            plt.clf()
            plt.plot(x_axis_data,y_axis_data)
            plt.ylabel('Trace (dB)')
            plt.xlabel('Frequency (Hz)')
       
        
        #plt.title(str(frequency) + ' THz', fontsize = 100)

      
        if (CB_state == True):
     
            if (get_axis_state == True):
                axis_matrix = plt.axis()
                get_axis_state = False
            if (axis_matrix[3] < 0):
                #plt.axis([centre-span/2, centre+span/2, axis_matrix[2]*1.05, axis_matrix[3]*0.9])
                plt.axis([centre-span/2, centre+span/2, axis_matrix[2]*1.0001, axis_matrix[3]*0.9])
            else:
                #plt.axis([centre-span/2, centre+span/2, axis_matrix[2]*0.95, axis_matrix[3]*1.02])
                plt.axis([centre-span/2, centre+span/2, axis_matrix[2]*0.9995, axis_matrix[3]*1.0001])
  
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
    np.savetxt(data_file, recorded_data, fmt='%.10e')
    file.close()
#
def free_run_plot_window_record_old(compensated, centre = 1.45*GHz, span = 0, full_span = 'N', record_length = 1*s):
    ''' Added by James, this is basically free_run_plot_window with the added feature of
    recording the data streamed. '''
    

    global CB_state
    CB_state = False
    global get_axis_state
    get_axis_state = True
    
    #Allows for two offsets, one dedicated as a fully span off set and the other
    #for various spans/frequencies
    if full_span == 'N':
        save_file = "C:\\Users\\Milos\Desktop\\Er_Experiment_Interface_Code\\amplitude_offset.csv"
    elif full_span == 'Y':
        save_file = "C:\\Users\\Milos\Desktop\\Er_Experiment_Interface_Code\\amplitude_offset_full.csv"   
    
    #adjust the plotted data to compensate for modulator RF and InGaAs detector response
    if compensated == 'Y':
        amplitude_offset = np.loadtxt(save_file,delimiter=",")
    
    #Traces are made up of 601 points (x axis) with a value from 0 to 610
    #This can be converted into dB
    SpecAn.write('LG?')
    dB_div = float(SpecAn.read())
    entire_depth = 10*dB_div #how many dB in the entire display
    SpecAn.write('RL?') #Get the reference level
    ref_level = float(SpecAn.read())
    
    lowest_point = ref_level - entire_depth 
    #To convert Y data to dB -> y_data*entire_depth/610 + lowest_point
    
    
    SpecAn.write('SP ' + str(span))
    SpecAn.write('CF ' + str(centre))
    
    #Data file set up
    data_file = "C:\Users\Milos\Desktop\James\\Time_series_data.csv" 
    day = time.strftime("%d")
    month = time.strftime("%m")
    year = time.strftime("%Y")
    hour = time.strftime("%H")
    minute = time.strftime("%M")
    second = time.strftime("%S")
    
    date_string = year + '-' + month + '-' + day
    time_string = hour + ":" + minute + "." + second
    SpecAn.write('CF?')
    center = float(SpecAn.read())
    SpecAn.write('ST?')
    sweep = float(SpecAn.read())
    SpecAn.write('SP?')
    span = float(SpecAn.read())
    
    try:
        os.remove(data_file)
    except OSError:
        pass
    file = open(data_file,'w')
    file.write(date_string + '\n')
    file.write(time_string + '\n')
    file.write('Time series recording of SpecAn. \n')
    file.write('Center Freq: ' + str(center) + '\n')
    file.write('Span: ' + str(span) + '\n')
    file.write('Sweep time: ' + str(sweep) + '\n')
    file.write('Time length of recording: ' + str(record_length) + '\n \n')
    
    #Number of loops needed to get required data
    loops = math.ceil(record_length/sweep) + 1
    loop_count = 0
    recorded_data = np.zeros((loops,601))
    
    while True:
        loop_count += 1
        #freq = Burleigh_WM.query_ascii_values("FETC:SCAL:FREQ?")
        #frequency = freq[0]
        
        SpecAn.write("TRA?")
        
        binary_string = SpecAn.read_raw()
        hex_string = binascii.b2a_hex(binary_string)
        y_axis_data = np.zeros(601)
 
        
        for i in range (601):
            
            y_axis_data[i] = int('0x' + hex_string[i*4: i*4+4], 0)
            
        x_axis_data = np.linspace(centre-span/2, centre+span/2, 601)
        y_axis_data = y_axis_data*entire_depth/610 + lowest_point #Convert to dB
        
        if loop_count < loops:
            recorded_data[loop_count,:] = y_axis_data
        
        #print y_axis_data
        if compensated == 'Y':
            compensated_data = np.subtract(y_axis_data,amplitude_offset)
            #we clear the figure before we plot, so that we dont replot over the 
            #old data 
            plt.clf()

            plt.plot(x_axis_data,compensated_data)
            plt.xticks(np.arange(min(x_axis_data), max(x_axis_data), (max(x_axis_data)-min(x_axis_data))/(2.9*5)))
            plt.ylabel('Trace - background (dB)')
            plt.xlabel('Frequency (Hz)')
        else:
            #we clear the figure before we plot, so that we dont replot over the 
            #old data 
            plt.clf()
            plt.plot(x_axis_data,y_axis_data)
            plt.ylabel('Trace (dB)')
            plt.xlabel('Frequency (Hz)')
       
        
        #plt.title(str(frequency) + ' THz', fontsize = 100)

      
        if (CB_state == True):
     
            if (get_axis_state == True):
                axis_matrix = plt.axis()
                get_axis_state = False
            if (axis_matrix[3] < 0):
                #plt.axis([centre-span/2, centre+span/2, axis_matrix[2]*1.05, axis_matrix[3]*0.9])
                plt.axis([centre-span/2, centre+span/2, axis_matrix[2]*1.0001, axis_matrix[3]*0.9])
            else:
                #plt.axis([centre-span/2, centre+span/2, axis_matrix[2]*0.95, axis_matrix[3]*1.02])
                plt.axis([centre-span/2, centre+span/2, axis_matrix[2]*0.9995, axis_matrix[3]*1.0001])
  
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
    np.savetxt(data_file, recorded_data, fmt='%.10e')
    file.close()
free_run_plot_window_record=free_run_plot_window_new



#
def data_plot_window(x_axis_data,y_axis_data, display_start, display_end):
    
    
    plt.clf()

    plt.plot(x_axis_data[display_start:display_end], y_axis_data[display_start:display_end])
    plt.xlim([centre-span*(0.5 - (float(display_start)/601)), centre+span*((float(display_end)/601) - 0.5)])
    #plt.ylim([0.4, 1])
    
    bexit = widget.Button(plt.axes([0.88, 0.91, 0.09, 0.07]), 'Quit', image=None, color=u'0.8', hovercolor=u'1')
    bexit.on_clicked(exit_button)
    plt.show()

#


#
def exit_button(arg):
    
    
    print 'exiting'
    
 
    
    #closes the visa session to the spectrum analyser if it is being used
        
    if (SpecAn_Bool == 1):
        SpecAn.close()
        print '-disconnected from HP8560E Spectrum Analyser'
        
    #if (Rigol_DMM_Bool == 1):
    #    Rigol_DMM.close()
    #    print '-disconnected from DMM'
    if (Stanford_Bool == 1):
        Stanford_FG.close()
        print '-disconnected from Stanford Function Generator'
 
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
def burn_scan_image_VCO(sweep_array,direction):
    
    global Agilent_OSA
    global Agilent_OSA_bool
    global SpecAn
    global SpecAn_Bool
    global Stanford_Bool
    global Stanford_FG

    #initialise the equiptment
    #Arduino = Initialise_Arduino(arduino_comport)
    #[Burleigh_WM, Burleigh_WM_bool] = Initialise_Burleigh_WM()
    [Agilent_OSA, Agilent_OSA_bool] = Initialise_OSA()
    [SpecAn, SpecAn_Bool] = Initialise_HP8560E_SpecAn()
    #[Stanford_FG, Stanford_Bool] = Initialise_Stanford_FG()

    
    #get the laser wavelength
    #Burleigh_WM.write("FETC:SCAL:WAV?")
    #laser_wavelength = np.float(Burleigh_WM.read())
    laser_wavelength = OSA_measure_wavelength(Agilent_OSA)
    #generate and upload the burn sweep to the Stanford and VCO
    #[num_array, waveform_length] = VCO_Sweep_backwards(sweep_array, Stanford_FG, Stanford_Bool)
    #Upload_to_Stanford_FG(num_array,waveform_length, Stanford_FG)
    
    #Arduino.write('0')
    #print Arduino.read() 
    #wait some time for the arduino to start the pulse program before setting trigger on SpecAn
    #time.sleep(1)

    #upload pulse sequence to Pulse Blaster (Burn, wait, Trigger SpecAn)

    pb.Sequence([(['ch1'], 3*s),
                    ([], 100*ms),
                    (['ch1', 'ch2', 'ch3'], 50*ms),
                    (['ch5'], 1*ms)],loop=False)
    #sends necessary pre-data collection settings to the Spectrum Analyser

    [SpecAn_BW, SpecAn_Sweeptime] = HP8560E_SpecAn_Resbandwidth_Sweeptime(10*kHz, sweeptime, SpecAn)
    [SpecAn_track, SpecAn_Power] = HP8560E_SpecAn_RF(tracking_gen, RF_power, SpecAn)
    [SpecAn_Centre, SpecAn_Span] = HP8560E_SpecAn_Centre_Span(centre, span, SpecAn)
    

    HP8560E_SpecAn_Trigger('EXT', 'SNGLS', SpecAn)
    #sets up registers to return interupt when sweep is complete
    SpecAn.write("CLEAR; RQS 4")
    #triggers spectrum analyser for data reading. it will no longer process input
    #untill the sweep has been triggered and completed
    SpecAn.write('TS')

    
    #Waits for Spectrum Analyser to finish Data sweep
    SpecAn.wait_for_srq(timeout = 30000)
    
    
    #generate the array to compensate for the RF and Detector response
    amplitude_offset = np.loadtxt("C:\\Users\\Milos\Desktop\\Er_Experiment_Interface_Code\\amplitude_offset.csv",delimiter=",")
    
    #collect trace data off spectrum analyser
    SpecAn.write("TRA?")
        
    binary_string = SpecAn.read_raw()
    hex_string = binascii.b2a_hex(binary_string)
    y_axis_data = np.zeros(601)
 
        
    for i in range (601):
            
        y_axis_data[i] = int('0x' + hex_string[i*4: i*4+4], 0)

    
    
    #divide by offset to compensate and generate an x_axis array
    y_axis_data = np.subtract(y_axis_data, amplitude_offset)
    x_axis_data = np.arange(centre-span/2, centre+span/2, span/601)
    #speed of light
    c = 299792453
    
    #generate absolute wavelength and frequency information based on direction of scan
    if direction == 'pos':
        wavelength_values = x_axis_data*((laser_wavelength**2)/(c*10**9))+laser_wavelength
       
        frequency_values = -x_axis_data + (c*10**9)/laser_wavelength
    else:
        wavelength_values = -x_axis_data*((laser_wavelength**2)/(c*10**9))+laser_wavelength
        frequency_values = x_axis_data + (c*10**9)/laser_wavelength
    
    filename =  "blank"

    save_data(filename, folder_name,  laser_wavelength,
    y_axis_data, wavelength_values, frequency_values)
    
    #turns off the RF and returns the spectrum analyser back to normal state.
    HP8560E_SpecAn_Trigger('FREE', 'CONTS', SpecAn)
    #[SpecAn_track, SpecAn_Power] = HP8560E_SpecAn_RF('OFF', RF_power, SpecAn)

            
    display_start = 1
    display_end = 601
    data_plot_window(x_axis_data,y_axis_data, display_start, display_end)
    
    

#


#
def burn_scan_image(burn_centre,burn_span,burn_power,direction):
    
    global SpecAn
    global SpecAn_Bool


    #initialise the equiptment
    Arduino = Initialise_Arduino(arduino_comport)
    [Burleigh_WM, Burleigh_WM_bool] = Initialise_Burleigh_WM()
    [SpecAn, SpecAn_Bool] = Initialise_HP8560E_SpecAn()


    #set the spectrum analyser sweeping to burn out a trench

    HP8560E_SpecAn_Trigger('FREE', 'CONTS', SpecAn)
    [SpecAn_track, SpecAn_Power] = HP8560E_SpecAn_RF('ON', burn_power, SpecAn)
    [SpecAn_BW, SpecAn_Sweeptime] = HP8560E_SpecAn_Resbandwidth_Sweeptime('AUTO', 300*ms, SpecAn)
    [SpecAn_Centre, SpecAn_Span] = HP8560E_SpecAn_Centre_Span(burn_centre, burn_span, SpecAn)

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
    

    time.sleep(5)

    #sends necessary pre-data collection settings to the Spectrum Analyser
    [SpecAn_Centre, SpecAn_Span] = HP8560E_SpecAn_Centre_Span(centre, span, SpecAn)
    [SpecAn_BW, SpecAn_Sweeptime] = HP8560E_SpecAn_Resbandwidth_Sweeptime(2*MHz, sweeptime, SpecAn)
    [SpecAn_track, SpecAn_Power] = HP8560E_SpecAn_RF(tracking_gen, RF_power, SpecAn)
    [SpecAn_Centre, SpecAn_Span] = HP8560E_SpecAn_Centre_Span(centre, span, SpecAn)
    

    HP8560E_SpecAn_Trigger('EXT', 'SNGLS', SpecAn)
    #sets up registers to return interupt when sweep is complete
    SpecAn.write("CLEAR; RQS 4")
    #triggers spectrum analyser for data reading. it will no longer process input
    #untill the sweep has been triggered and completed
    SpecAn.write('TS')

    
    #Waits for Spectrum Analyser to finish Data sweep
    SpecAn.wait_for_srq(timeout = 100000)
    
    
    #generate the array to compensate for the RF and Detector response
    amplitude_offset = np.loadtxt("C:\\Users\\Milos\Desktop\\Er_Experiment_Interface_Code\\amplitude_offset.csv",delimiter=",")
    
    #collect trace data off spectrum analyser
    SpecAn.write("TRA?")
        
    binary_string = SpecAn.read_raw()
    hex_string = binascii.b2a_hex(binary_string)
    y_axis_data = np.zeros(601)
 
        
    for i in range (601):
            
        y_axis_data[i] = int('0x' + hex_string[i*4: i*4+4], 0) + 65536

    
    
    ##divide by offset to compensate and generate an x_axis array
    ##y_axis_data = np.divide(y_axis_data, amplitude_offset)
    x_axis_data = np.arange(centre-span/2, centre+span/2, span/601)
    #speed of light
    c = 299792453
    
    #generate absolute wavelength and frequency information based on direction of scan
    if direction == 'pos':
        wavelength_values = x_axis_data*((laser_wavelength**2)/(c*10**9))+laser_wavelength
       
        frequency_values = -x_axis_data + (c*10**9)/laser_wavelength
    else:
        wavelength_values = -x_axis_data*((laser_wavelength**2)/(c*10**9))+laser_wavelength
        frequency_values = x_axis_data + (c*10**9)/laser_wavelength
    
    filename =  "polarised spectrum positive 1"

    save_data(filename, folder_name,  laser_wavelength,
    y_axis_data, wavelength_values, frequency_values)
    
    #turns off the RF and returns the spectrum analyser back to normal state.
    HP8560E_SpecAn_Trigger('FREE', 'CONTS', SpecAn)
    [SpecAn_track, SpecAn_Power] = HP8560E_SpecAn_RF('OFF', RF_power, SpecAn)

            
    display_start = 1
    display_end = 601
    data_plot_window(x_axis_data,y_axis_data, display_start, display_end)
    
    

#


def spectrum_image(avg_num,direction):
    
    
    pylab.ion()
    
    [Burleigh_WM, Burleigh_WM_bool] = Initialise_Burleigh_WM()
    [SpecAn, SpecAn_Bool] = Initialise_HP8560E_SpecAn()

    #set the spectrum analyser scanning
    HP8560E_SpecAn_Trigger('FREE', 'CONTS', SpecAn)
    
    [SpecAn_BW, SpecAn_Sweeptime] = HP8560E_SpecAn_Resbandwidth_Sweeptime(resbandwidth, sweeptime, SpecAn)
    [SpecAn_Centre, SpecAn_Span] = HP8560E_SpecAn_Centre_Span(centre, span, SpecAn)
    [SpecAn_track, SpecAn_Power] = HP8560E_SpecAn_RF(tracking_gen, RF_power, SpecAn)
     
    #need initial x_axis measurements to generate output array
    x_axis_data = np.arange(centre-span/2, centre+span/2, span/601)
       
    #load in the offset from InGaAs detector and Modulator response
    amplitude_offset = np.loadtxt("C:\\Users\\Milos\Desktop\\Er_Experiment_Interface_Code\\amplitude_offset.csv",delimiter=",")
         
    compensated_array = np.zeros((avg_num,601),dtype=float)
        
    c = 299792453
         
     
    Burleigh_WM.write("FETC:SCAL:WAV?")
    laser_wavelength = np.float(Burleigh_WM.read())

    
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
        
        #collect data from spectrum analyser
        SpecAn.write("TRA?")
        binary_string = SpecAn.read_raw()
        hex_string = binascii.b2a_hex(binary_string)
        spec_data_temp = np.zeros(601)
 
        for j in range (601):
            
            spec_data_temp[j] = int('0x' + hex_string[j*4: j*4+4], 0)
            
        compensated_data = np.subtract(spec_data_temp,amplitude_offset)
             
        compensated_array[i,:] = compensated_data[:]
        plt.plot(wavelength_values,compensated_data)
        plt.pause(0.01)
       
       
    #turn off RF so it stops burning
    [SpecAn_track, SpecAn_Power] = HP8560E_SpecAn_RF('OFF', RF_power, SpecAn)   
    
    #average the above runs into one array
    avg_spec_data = np.average(compensated_array,0)
        
    #print avg_spec_data
        
    plt.clf()
    pylab.ioff()
    
    foldername = 'spin polarisation image'
    filename = 'unpolarised-negative direction'
    
    
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


#
def run_arduino():
 
    Arduino = Initialise_Arduino(arduino_comport)
    
    time.sleep(1)
    Arduino.write('0')
    print Arduino.read()
#
#need to execute code as a try/except statement, otherwise if you break the code manually,
#visa seems to not return the instrument handles. This causes the GPIB card to freeze,
#so the PC must be restarted before you can run the program again...annoying




## #input the spectrum span and centre frequency in Hz
## SpecAn.write("SP?")
## span = SpecAn.read()
## SpecAn.write("CF?")
## centre = SpecAn.read()
## SpecAn.write("RB?")
## resbandwidth = SpecAn.read() # in Hz, otherwise set to 'AUTO'



## #span = 5*MHz
## #centre = 1150*MHz
## SpecAn.write("SRCPWR?")
## RF_power = SpecAn.read() #in dBm
## SpecAn.write("ST?")
## sweeptime =  SpecAn.read() #in seconds, otherwise set to 'AUTO'



## #input whether to turn on tracking generator and specify the RF power in dBm
## tracking_gen = 'ON'  #accepts 'ON' or 'OFF'



## #folder_name = "200 uW burn power, +1 only (2.3-3.0GHz)"
## folder_name = "positive side polarisation"
## #inputs triggering options, see "Intro to Spec An commands"
## trig_source = "EXT"
## trig_type = "SING"
## trig_polarity = "POS"

## #input stanford parameters for VCO burn (1.726 to 3.897 GHz). each section corresponds to one sweep section
sweep_array = np.array([[1.9*GHz, 2.9*GHz, 300*ms]])

## #input stanford parameters for Backwards VCO burn (0.865 to 2.334 GHz). each section corresponds to one sweep section
## sweep_array = np.array([[1.3*GHz, 2.3*GHz, 100*ms]])

try: 

       

#############CHOOSE ONE OF THE FOLLOWING TO EXECUTE###############
    variable_to_make_this_do_nothing = 0
##     free_run_plot_window('N', 1.45*GHz, 2.9*GHz) #choose 'Y' or 'N' to compensate  the plotted data 
##     free_run_plot_window_record('N', centre = 1.45*GHz, span = 0, full_span = 'N', record_length = 1*s)
    
    #for modulator RF and InGaAs detector response 
    #save_offset(20)  #number of background runs to average so to make clean background trace
    #spectrum_image(3,'neg')

    #T2_Pulse_Sequence()
    #burn a deep trench then scan image, 
    
    #burn_scan_image_VCO(sweep_array, 'pos')
    
    #burn_scan_image(350*MHz, 600*MHz, 2, 'neg')  #burn_centre, burn_span, burn_power, direction
    #pb.Sequence([(['ch1', 'ch2','ch4'], 1*s)],loop=True)
    #run_arduino()

 
    
except KeyboardInterrupt:
    print 'failed'
    del HP_SpecAn



if __name__=="__main__":
##     free_run_plot_window(False)
    x = 1
