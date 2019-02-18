# -*- coding: utf-8 -*-
"""
Created on Thu Jan 24 16:21:09 2019
Simple script which takes heterodyne measurements from the picoscope and plots them
@author: James
"""

from matplotlib.pyplot import *
import numpy as np
from unloadmat import unloadmat
import FiberDetCal as detCal

folder = r'C:\Users\James\Desktop\Work\19-01 QAFC prep\19-01-22 SSB shot noise\SSB change LO power\\'
files = os.listdir(folder)

nfft = 2**12
i = 0
for file in files:
    print('Processin file {:s}...'.format(file))
    D,t,A,B = unloadmat(folder+file) #Replace this with A,B from picoscope stream 
    
    cal = np.sqrt(np.mean(A**2)/np.mean(B**2))
#     A,B,t=detCal.cal_det_f2(D)
    
    B*=cal
    
    
#     figure(2*i)
    figure(1)
    ampA,f=psd(A, nfft, Fs = 1/t[1], scale_by_freq=True, label = file)
    close(1)
    figure(2,figsize=[10,5])
    semilogy(f,ampA,label=file)
    title('Unbalanced PSD')
    xlim((0,30e6))
    ylabel('PSD (dB/Hz)')
    xlabel('Frequency (Hz)')
    grid()
    legend()
    
#     figure(3)
    figure(1)
    amp,f=psd(A-B, nfft, Fs = 1/t[1], scale_by_freq=True, label = file)
    close(1)
    figure(3,figsize=[10,5])
    semilogy(f,amp, label = file)
    title('Balanced PSD ' +str(file))
    xlim((0,30e6))
    ylabel('PSD (dB/Hz)')
    xlabel('Frequency (Hz)')
    grid()
    legend()
    
    
    i+=1