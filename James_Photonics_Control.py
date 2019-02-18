# -*- coding: utf-8 -*-
"""
Created on Sun Sep 30 17:33:35 2018
James's Version of the Photonics controller
@author: James
"""
from time import sleep
import purephotonicscontrol.ITLA_Wrap as ITLA_Wrap

def PhotonicsLaser(ITLA_class = None, on = True, freq = 194.9412, power = 1600, sweep = [False,0,0], jump=None, whisperMode = True):
    ''' This should do every basic thing you want the laser to do
        on = T/F. Turn the laser on or off
        freq = set frequency (THz)
        power = set power (100*dBm)
        sweep = set sweep parameters [T/F,Range(GHz),speed(MHz)]
        TODO: add jump.
    '''
    
    #Opens the photonics laser if needed
    if ITLA_class == None:
        ITLA = ITLA_Wrap.ITLA_Class(port="COM6",baudrate=9600) #Open the Photonics Laser
    else:
        ITLA = ITLA_class
    ITLA.ProbeLaser()    #Probe laser and check it's happy
    
    if on:
        ITLA.EnableLaser(False) #Make sure lasers off before setting parameters
        
        #Set Frequency and Power
        ITLA.SetFrequency(freq) #THz
        ITLA.SetPower(power) #dBm * 100    
        
        if sweep[0]: #Set sweep parameters
            ITLA.SetSweepRange(sweep[1]) #GHz
            ITLA.SetSweepRate(sweep[2])  #MHz
            
            
        ITLA.EnableLaser(True)
        ITLA.EnableWhisperMode(whisperMode) 
        sleep(0.1)
        
        if sweep[0]:
            print('Enabling sweep.')
            ITLA.EnableSweep(True)    
            
        else:
            ITLA.EnableSweep(False)#Make sure laser not sweeping.
            
    
    
    else: #Turn off the laser
        ITLA.EnableSweep(False)
        ITLA.EnableWhisperMode(False)
        ITLA.EnableLaser(False)        
        
    return ITLA


def PhotonicsError(ITLA ):
    
    print(ITLA.ITLALastError())
    return(ITLA.ITLALastError())
        
    