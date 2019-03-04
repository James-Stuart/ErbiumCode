# -*- coding: utf-8 -*-
"""
Created on Mon Mar 04 09:14:31 2019
Phonon experiment code
@author: James
"""

import HP8560E_Spectrum_Analyser as HP
#import spectrum_image_HP8560E as spec #Dont use free run with long scan times
import PhotonicsSweepRecord as phot
import pulse_blaster as pb
import scipy.io as sio 
import time


def setUpSpec(freq = 1e9, rl = 1e-4):
    SpecAn,boool = HP.Initialise_HP8560E_SpecAn()
    RefLevelStr = 'RL ' + str(rl) + ' V' 
    FreqStr = 'CF ' + str(freq)
    
    #Reference level is linear and between 1e-3, 1e-5
    #Span is 0 and set to given frequency, sweep time is long as possible (100s)
    SpecAn.write('LN') #Change SpecAn to linear
    SpecAn.write(RefLevelStr)
    SpecAn.write('SP 0')
    SpecAn.write(FreqStr)
    SpecAn.write('ST 100')
    
    
    return SpecAn
    
def gatePump(gateFreq=30):
    t = 1./(2*gateFreq)
    pb.Sequence([(['ch6','ch7'], t) , ([], t)], loop=True)
    
    
def runLasers(probeF = 194.941,pumpF = 194.941,field = 0,temp = 520,
              lockinTC = 0.3,lockinVrange = 0.05,lockinSen = 12):
    
    ProbeSidabandActual,RlActual = getProbefRL()
    #~~~~~~~~~~~~~~~~~~~~~~~~~~ CHANGE AS NEEDED ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ 
    ExperimentSettings = {'Time Constant':lockinTC , 'Volt Range':lockinVrange , 'Sensitivity': lockinSen,
                          'Refernece Level':RlActual , 'Probe Sideband':ProbeSidabandActual ,
                          'Probe Laser Freq': probeF , 'Pump Laser Freq': pumpF ,
                          'Field':field , 'Cryostat Thermistor':temp}
    
    fNameSuf = str(field) +'T, '+str(probeF) + 'THz'
    #Save experiment settings
    date = time.strftime('%y-%m-%d')
    filenameMat = "C:\Users\Milos\Desktop\James\\" + date + ' ' + fNameSuf + 'experiment settings.mat'
    sio.savemat(filenameMat,ExperimentSettings)
    
    #Sweep probe 
    phot.recSweepOffs(f=probeF,p = 1200,sweep=[True,10,10000],RecordLength=None,fName=fNameSuf + ' probe freq')
    
    #save pico scan
    #fNamePico = fNameSuf + ' pico'
    print(str(field) +'T, '+str(probeF) + 'THz recorded.')
    
    

def expSetup(ProbeSideband=1e9,rl=1e-4):
    #Run this for initial set up
    
    #Cool cryostat to ~520 OHMs
    #Set specan to linear (code)
    #Manually set LockIn to 50mV sensitivity 12dB with 300ms time constant
    #Probe into cryostat via phase mod, at ~1GHz
    #pump into cryo in other direction (going through mems), gated at 30Hz (code)
    #Set magnetic field
    #Sweep probe over one of the zeeman arms and move pump until maximum signal is achieved (+/- 0.5GHz)
    #Probe into fast det, into SpecAn, video out into pico and lockin
    #Lockin locked to pump gate, output into pico
    #Record pico and sync with probe scan
    

    setUpSpec(freq = ProbeSideband,rl=rl)
    gatePump()
    print('Experiment setup complete.')


def getProbefRL(SpecAn):
    FreqActual = SpecAn.query('CF?')
    RlActual = SpecAn.query('RL?')
    return FreqActual,RlActual