# -*- coding: utf-8 -*-
"""
Created on Mon Oct 29 11:18:51 2018
Take in .mat data and plot data and fft
@author: James
"""

import scipy.io as sci
import numpy as np
import matplotlib.pyplot as plt

def matFFTplot(fileloc,dictkey='',fs=1e5):
    
    if dictkey == '':
        dictkey = 'A'
        
    tempDict = sci.loadmat(fileloc)
    data = tempDict[dictkey]
    data = data.squeeze()
    
    amp,f=plt.psd(data,NFFT=2**20,Fs=fs,scale_by_freq=True)
    plt.close()
    
    plt.figure()
    plt.semilogy(f[1:],amp[1:])
    plt.xlim((0,20))
    
    
    plt.figure()
    plt.plot(data)
    plt.title('Raw Data')
    plt.show()
    
    
    
    
    
    