###############################################################################
#                                                                             #
#                            NEW LASER CONTROLLER                             #      
#                     (I really hope Matt's code works)                       #
#                                                                             #
###############################################################################
from matplotlib import pyplot as plt
import math
import ITLA_Wrap_v3_MattB as ITLA  
import time
import logging
from visa import *

Hz = 1
kHz = 1e3
MHz = 1e6
GHz = 1e9

hour = 3600
min = 60
s = 1
ms = 1e-3
us = 1e-6
ns = 1e-9




def init_laser_sweep(set_freq = 195.50,sweep_range = 1.5,sweep_time = 100*ms,power=1800):
    '''Initialises the small 1550 nm laser.
    set_freq is in THz
    Sweep_range is in GHz
    sweep_time is in seconds
    and power is in dBm x 100
    '''
    
    logging.basicConfig(level=logging.INFO, filename="logfile_"+time.strftime('%d%b%Y'), filemode="a+", format="%(asctime)-15s %(levelname)-8s %(message)s")
                        
    #Gives the sweep rate in MHz/s
    sweep_rate = sweep_range*1e3/sweep_time
    
    #Connect to laser and scope
    laser = ITLA.ITLAConnect("COM6",9600)
    rm = ResourceManager();
        
    #Probe laser and check it's behaving
    ITLA.ProbeLaser(laser)
    ITLA.EnableLaser(laser,False)
    #Centre frequency in THz
    #195.60 THz should be centre of some line
    ITLA.SetFrequency(laser,set_freq)
    #Sweep range in GHz
    ITLA.SetSweepRange(laser,sweep_range)
    #Max sweep rate in MHz/s
    ITLA.SetSweepRate(laser,sweep_rate)
    #Laser power in dBm
    ITLA.SetPower(laser,power)
    #Turn on laser
    ITLA.EnableLaser(laser,True)
    print "Laser Sweep Initialised"
    return laser
    

def SweepSequence_start(laser):
    init_laser_sweep(set_freq = 195.50,sweep_range = 1.5,sweep_time = 100*ms,power=1800)
    ITLA.EnableWhisperMode(laser,True)
    time.sleep(1)
    ITLA.EnableSweep(laser,True)
    print 'Starting sweep, use PulseBlaster channel 6 to activate' 

def SweepSequence_stop(laser)
    ITLA.EnableSweep(laser,False)
    ITLA.EnableWhisperMode(laser,False)
    print 'Stopping sweep, goodbye world!'
    