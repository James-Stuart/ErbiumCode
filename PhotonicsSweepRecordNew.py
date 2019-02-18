# -*- coding: utf-8 -*-
"""
Created on Mon Oct 08 13:35:39 2018

@author: James
"""

import purephotonicscontrol.ITLA_Wrap as ITLA_Wrap
# =============================================================================
# import picoscope_runner as pico
# import pulse_blaster as pb
# =============================================================================
import time
from time import sleep
import numpy as np
import os

def photonicsControl(freq = 194.9412, power = 1600, sweep=[False,0,0]):
    ITLA = ITLA_Wrap.ITLA_Class(port="COM5",baudrate=9600) #Open the Photonics Laser
    #Probe laser and check it's happy
    ITLA.ProbeLaser()    
    #Disable laser to change parameters
    ITLA.EnableLaser(False)    
    
    ITLA.SetFrequency(freq) #THz
    ITLA.SetPower(power) #dBm * 100     
    
    if sweep[0]:
        ITLA.SetSweepRange(sweep[1])
        ITLA.SetSweepRate(sweep[2])
        print('sweeping {:.1f} GHz at a rate of {:.1f} GHz/s.'.format(sweep[1],sweep[2]/1000))
    else:
        print('with sweeping disabled.')
        
    ITLA.EnableLaser(True)     
    ITLA.EnableWhisperMode(True) 
    sleep(0.1)
    ITLA.EnableSweep(True)    
    
    return ITLA
        
    
def photonicsOff(ITLA):    
    ITLA.EnableSweep(False)
    ITLA.EnableWhisperMode(False)
    ITLA.EnableLaser(False)
    

def photonicsSweepPicoRecord(f,p,sweep,fOffsRecordLength=10,fName = ''):
    tDiff =0
    tArr = np.empty(0)
    offsArr = np.empty(0)
    
    print('Make sure picoscope is set to EXT trig')
    ITLA = photonicsControl(f,p,sweep)
    time.sleep(0.01) #Small delay between sweep starting and querying freq offs
    tStart = time.time()
# =============================================================================
#     pb.Sequence([(['ch3','ch6'], 0.01)], loop = False) #Trigger PB
# =============================================================================
    
    while tDiff < fOffsRecordLength:    
        offsArr=np.append(offsArr,ITLA.ReadOffsetFreq())        
        tDiff = time.time()-tStart
        tArr=np.append(tArr,tDiff)
        
        time.sleep(0.01)
        
    data = np.vstack([tArr, offsArr]).T
    
    #Create file and save
    date = time.strftime('%y-%m-%d')
    filename = r"C:\Users\adam\Desktop\James' Secrets\\" + date + ' ' + fName +'.txt'
    try:
        os.remove(filename)
    except OSError:
        pass    

    file = open(filename, 'a')
    file.write('Time: ' + str(tStart) + '\n')
    file.write('CenterF: ' + str(f) + '\n')
    file.write('Sweep: ' + str(sweep[2]) + '\n')
    file.write('Sweep rate: ' + str(sweep[1]) + '\n')
    file.write('\n')
    np.savetxt(file, data)
    
    file.close()
    photonicsOff(ITLA)
    
    return data

def testingSweepRead(ITLA,RecordLength=10,fName = ''):
    tDiff =0
    tArr = np.empty(0)
    offsArr = np.empty(0)
    
    time.sleep(0.01) #Small delay between sweep starting and querying freq offs
    tStart = time.time()
# =============================================================================
#     pb.Sequence([(['ch3','ch6'], 0.01)], loop = False) #Trigger PB
# =============================================================================
    
    while tDiff < RecordLength:    
        offsArr=np.append(offsArr,ITLA.ReadOffsetFreq())        
        tDiff = time.time()-tStart
        tArr=np.append(tArr,tDiff)
        
        time.sleep(0.01)
        
    data = np.vstack([tArr, offsArr]).T
    
    #Create file and save
    date = time.strftime('%y-%m-%d')
    filename = r"C:\Users\adam\Desktop\James' Secrets\\" + date + ' ' + fName +'.txt'
    try:
        os.remove(filename)
    except OSError:
        pass    

    file = open(filename, 'a')
    file.write('Time: ' + str(tStart) + '\n')

    file.write('\n')
    np.savetxt(file, data)
    
    file.close()
    
    return offsArr
    
    