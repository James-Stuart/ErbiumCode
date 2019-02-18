# -*- coding: utf-8 -*-
"""
Created on Mon Oct 08 13:35:39 2018

@author: James
"""

import purephotonicscontrol.ITLA_Wrap as ITLA_Wrap
import pulse_blaster as pb
import time
from time import sleep
import numpy as np
import os
import scipy.io as sio 
import picoscope_runner as pico
import matplotlib.pyplot as plt
#TODO: add picoscope control, if I feel like it.

def photonicsControl(freq = 194.9412, power = 1600, sweep=[False,0,0]):
    ITLA = ITLA_Wrap.ITLA_Class(port="COM6",baudrate=9600) #Open the Photonics Laser
    #Probe laser and check it's happy
    ITLA.ProbeLaser()    
    #Disable laser to change parameters
    ITLA.EnableLaser(False)    
    
    ITLA.SetFrequency(freq) #THz
    ITLA.SetPower(power) #dBm * 100     
    print('Photonics Laser set to {:.4f} THz at {:.0f} dBm,'.format(freq,power/100))
    
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
    
    
    

def photonicsSweepPicoRecord(f,p,sweep,fOffsRecordLength=12,fName = '',showDataPlot = False, openP = False):
    if 'ps' not in globals():
        global ps
        ps = pico.open_pico()
        
    if openP:
        ps = pico.open_pico()
    
    
    tDiff =0
    tArr = np.empty(0)
    offsArr = np.empty(0)


    ITLA = photonicsControl(f,p,sweep)
    time.sleep(0.1)
       
    print('Setting up picoscope collection')
    t_s = 100e-6
# =============================================================================
#     r_l = 10 #~100,000 data points
# =============================================================================
    r_l = 100 #1,000,000 data points
# =============================================================================
#     r_l = 20 #200,000 data points
# =============================================================================
    chB = [True,20]
    t_sample,res = pico.run_rapid_block(ps, Vrange = 5, n_captures = 1, t_sample = t_s, record_length = r_l, chB=chB)
    
    time.sleep(0.1)    
    
    tStart = time.time()
    pb.Sequence([
        (['ch3','ch5','ch2'], 0.01), 
        (['ch5','ch2'], 0.01)], 
        loop = False) #Trigger PB
    
    while tDiff < fOffsRecordLength:    
        offsArr=np.append(offsArr,ITLA.ReadOffsetFreq())        
        tDiff = time.time()-tStart
        tArr=np.append(tArr,tDiff)
        
        time.sleep(0.01)
        
    data = np.vstack([tArr, offsArr]).T
    
    print('Formatting and saving data')
    dataPicoA,dataPicoB = pico.get_data_from_rapid_block(ps)
    t = np.arange(dataPicoA.shape[0])*t_s
    data_total = np.vstack([t,dataPicoA,dataPicoB])
    data_total = data_total.T
    
    
    date = time.strftime('%y-%m-%d')
    #Save laser freq offset and pico data
    filenameMat = "C:\Users\Milos\Desktop\James\\" + date + ' ' + fName + '.mat'
    sio.savemat(filenameMat,{'Time':tStart,'CenterF':f,'Sweep':sweep[2],'SweepRate':sweep[1],'DataSweep':data, 'DataPico':data_total})
    
    
    if showDataPlot:
        plt.plot(data.T[1])
        plt.show()
    
    photonicsOff(ITLA)
    
    return data,ps


def SweepManyFreq(fList=[], fileAffix ='',openP = False):
# =============================================================================
#     import Rigol_DMM as rigol
#     rigol_DMM,b = rigol.Initialise_DMM()
# =============================================================================
    
    if len(fList) == 0:
        fList = np.arange(-5,6)*0.05+194.9412 #250GHz either side of 194.9412 in 50GHz steps
    for f in fList:
        print('\n Starting Freq: ' + str(f) +' \n')
        
        if fileAffix == '':
            fName = str(f) + ' 7T, 2kOHM'
        else:
# =============================================================================
#             R = rigol.Rigol_Query_R_simple(rigol_DMM)
#             print('Resistance: ' + str(R))
#             R = round(R)
#             R *= 1e-3
# =============================================================================
            fName = str(f) + ' '+ fileAffix
            
# =============================================================================
#         data,ps=photonicsSweepPicoRecord(f,1200,[True,60,20000],20,fName,False,openP)
# =============================================================================
# =============================================================================
#             data,ps=photonicsSweepPicoRecord(f,1200,[True,60,2000],50,fName,False,openP)
# =============================================================================
            data,ps=photonicsSweepPicoRecord(f,1200,[True,60,8000],20,fName,False,openP)
    
    return ps
    #ps.close()
    
def RecEvery10min(n=''):
    
    if n == '':
        n = 9
    
    for i in range(n):
        ps = SweepManyFreq(fList = [194.9412], fileAffix = '7T, ')
        sleep(300)
    return ps
        


def testingSweepRead(ITLA,RecordLength=10,fName = ''):
    '''Make sure laser is on and sweeping.'''
    tDiff =0
    tArr = np.empty(0)
    offsArr = np.empty(0)
    
    time.sleep(0.01) #Small delay between sweep starting and querying freq offs
    tStart = time.time()
   
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
    
    import matplotlib.pyplot as plt
    plt.plot(offsArr)
    plt.show()
    
    return offsArr


def recSweepOffs(f,p,sweep,RecordLength=None,fName='',):
    '''Set the photonics laser to sweep for a given amount of time.
    f = frequency of the alser (194.941 THz)
    p = power (1600 dBm/100)
    sweep = [T/F,Range(GHz),SweepRate(MHz/s)]
    RecordLength = None default, will sweep until interrupted. Or give it a set time.
    fName = file name.
    '''
    ITLA = photonicsControl(f,p,sweep)
    time.sleep(0.1)
    
    tDiff = 0
    tArr = np.empty(0)
    offsArr = np.empty(0)
    date = time.strftime('%y-%m-%d')
    filenameMat = "C:\Users\Milos\Desktop\James\\" + date + ' ' + fName + '.mat'
    tStart = time.time()
    
    if RecordLength is None:
        #Record until interrupted
        try:    
            while 1:
                offsArr=np.append(offsArr,ITLA.ReadOffsetFreq())        
                tDiff = time.time()-tStart
                tArr=np.append(tArr,tDiff)
            
                time.sleep(0.1)   
            
        except KeyboardInterrupt():
            pass
        finally:
            #once interrupted save data
            data = np.vstack([tArr, offsArr]).T
            sio.savemat(filenameMat,{'Time':tStart,'CenterF':f,'Sweep':sweep[2],'SweepRate':sweep[1],'DataSweep':data})
            print('Picoscope sweeping offset recorded for ' + str(tDiff) + 's.')
        
    elif isinstance(RecordLength, float) or isinstance(RecordLength, int):
        #Record for given amount of time
        while tDiff < RecordLength:    
            offsArr=np.append(offsArr,ITLA.ReadOffsetFreq())        
            tDiff = time.time()-tStart
            tArr=np.append(tArr,tDiff)
            
            time.sleep(0.1)  
        
        data = np.vstack([tArr, offsArr]).T
        sio.savemat(filenameMat,{'Time':tStart,'CenterF':f,'Sweep':sweep[2],'SweepRate':sweep[1],'DataSweep':data})
            
    else:
        raise ValueError('RecordLength must be a number.')
    
    #Finally turn off the laser
    photonicsOff(ITLA)
    
    
    
    
    
    