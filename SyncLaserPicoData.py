# -*- coding: utf-8 -*-
"""
Created on Mon Mar  4 13:28:10 2019
Takes in two data files from the phonon experiment (probe laser sweep data and picoscope data)
and syncs the times of each file (interpolating and cropping the probe laser data).
Outputs the relavent data and time arrays.
@author: James
"""

def SyncLaserPicoData(picoFileLoc,laserFileLoc):
    '''Pico file should be saved as an h5 file type from DAMpico, whilst
    probe laser file should be a .mat'''
    import h5py
    import scipy.io as sio
    import numpy as np
    from scipy.interpolate import interp1d
    
    #load files
    picoDict = h5py.File(picoFileLoc)
    laserDict = sio.loadmat(laserFileLoc)
    picoData = picoDict['Export']
    
    #pico data
    picoT = picoData[0]
    picoAmp = picoData[1]

    #Laser data format
    #'Time':tStart,'CenterF':f,'Sweep':sweep[2],'SweepRate':sweep[1],'DataSweep':data    
    laserStart = laserDict['Time'][0]
    laserTnoOffs = laserDict['DataSweep'][:,0]
    laserT = laserTnoOffs + laserStart
    laserSweep = laserDict['DataSweep'][:,1]
    
    
    #Time difference between the start of each recording
    diffT = picoT[0]-laserT[0]
    diffTend = picoT[-1]-laserT[0]
    indexStart = np.searchsorted(laserTnoOffs, diffT) #laser index closest to pico start
    
    #Ensures the cropped laser data is always longer than the pico data 
    try:
        indexEnd =  np.searchsorted(laserTnoOffs, diffTend)+1 #laser index closest to pico end
    except:
        indexStart -=1 #If you cant add 1 to indexEnd, minus 1 from IndexStart
    
    #crop laser data
    laserCropped = laserSweep[indexStart:indexEnd]
    laserCroppedT = laserTnoOffs[indexStart:indexEnd]
    laserCroppedT -= laserCroppedT[0]
    
    #interpolate
    f=interp1d(laserCroppedT,laserCropped)
    laserInterp = f(picoT-picoT[0])
    
    return picoT,picoAmp,laserInterp
    


if __name__ == '__main__':
    picoFile = r'C:\Users\James\Documents\testData\testPicoData.h5'
    laserFile = r'C:\Users\James\Documents\testData\19-02-18 .mat'
    
    t,p,l,told,lold=SyncLaserPicoData(picoFile,laserFile)
    
    from matplotlib.pyplot import *
    
    plot(t-t[0],l)
    
    