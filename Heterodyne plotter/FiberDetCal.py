# -*- coding: utf-8 -*-
"""
Created on Tue Dec 18 11:45:47 2018
These functions are for the purpose of balancing the two 1550nm, 30MHz fiber 
coupled photo detectors.
@author: James
"""


def intp_freq_response(f_array):
    '''Takes in a frequency array and interpolates the "FiberDetectorFrequencyResponse"
    to match this array.
    
    The detector responses were recorded between 1 and 30MHz, but accuracy below 5 MHz is questionable.
    Assumes that f_array strictly increases.'''
    import numpy as np
    
    if min(f_array) > 1e6:
        raise RuntimeError('Frequency at least go below 1MHz')
    if max(f_array) < 3e7:
        raise RuntimeError('Frequency at least go beyond 30MHz')
    
    
    #Find when f_array is near 1MHz
    i = -1
    x = 0
    while x < 1e6:
        i +=1
        x = f_array[i]
    
    #Find when f_array is near 30MHz
    j = -1
    x = 0
    while x < 3e7:
        j +=1
        x = f_array[j]
    
    #Get f_array between 1 - 30 MHz
    f = f_array[i:j]
    
    #Load the interpolated frequency responses, note "det2" is the detector labelled B
    det1 = np.load(r'C:\Users\James\Desktop\Work\18-07 Locking Photonics\det1.npy')
    det2 = np.load(r'C:\Users\James\Desktop\Work\18-07 Locking Photonics\det2.npy')
    det1 = det1[()]
    det2 = det2[()]
    
    y1 = det1(f)
    y2 = det2(f)
    
    index_start = i
    index_end = j
    
    return y1,y2,index_start,index_end





def cal_det_f(Dict,nfft = 2**12,flip=False,cal=1):
    '''Takes in .mat Dictionary from picoscope and calibrates 
    based on detector freq response, and returns the calibrated FFT spectrum
    
    NFFT, sets the frequency resolution of the output 
    cal, the difference in signal size between channels B and A (specifically 
    B_calibrated = B*cal).
    
    Code assumes CHA = det1 and CHB = det2. if not then make flip != False'''
    import matplotlib.pyplot as plt
    
    B = Dict['B'].squeeze()
    A = Dict['A'].squeeze()
    t_int = Dict['Tinterval'].squeeze()
    
    B*=cal
    
    #messy but works
    if flip != False:
        c = B
        B = A
        A = c
    
    plt.figure(1)
    ampb,fb = plt.psd( B, nfft, Fs=1/t_int, scale_by_freq=True)  
    ampa,fa = plt.psd( A, nfft, Fs=1/t_int, scale_by_freq=True)  
    plt.close(1)
    
    y1,_,i1,j1 = intp_freq_response(fa)
    _,y2,i2,j2 = intp_freq_response(fb)
    
    AmpCalA = ampa[i1:j1]/y1
    AmpCalB = ampb[i2:j2]/y2
    f = fa[i1:j1]
    
    return AmpCalA,AmpCalB,f
    


def cal_det_f2(Dict, flip = False):
    ''' Redeisgn to treat the detector frequency response as a convolution mask
    between 0 - 30MHz, where (due to spectrum analyzer inaccuracies) frequencies
    below 1MHz are not effected.
    
    Dict, .mat dictionary from picoscope
    Code assumes CHA = det1 and CHB = det2. if not then make flip != False
    
    added 18-12-18.
    
    TODO: add exception for data sets that dont go out to 30MHz.
    '''
    import numpy as np
    
    A = Dict['A'].squeeze()
    B = Dict['B'].squeeze()
    t_int = Dict['Tinterval'].squeeze()
    t = np.linspace(0,t_int*len(A),len(A))
    
    if t_int > 1/30e6:       
        raise RuntimeError('Frequency at least go beyond 30MHz')
        
    #messy but works
    if flip != False:
        A,B = B,A

        
    f_array = np.fft.fftfreq(len(A),t_int)
    #Find when f_array is near 30MHz
    j = f_array[:round(len(f_array)/2-1)].searchsorted(30e6, side = 'right')
    f = f_array[:j]

    
    #Load the interpolated frequency responses, note "det2" is the detector labelled B
    #Response  runs from 0 - 30MHz.
    det1 = np.load(r'C:\Users\James\Desktop\Work\18-07 Locking Photonics\det1DC.npy')
    det2 = np.load(r'C:\Users\James\Desktop\Work\18-07 Locking Photonics\det2DC.npy')
    det1 = det1[()]
    det2 = det2[()]
    
    
    det1intp = det1(f)
    det2intp = det2(f)
    
    #Creates a frequency response array thay goes beyond 30MHz, to preserve shape 
    det1convMask = np.ones(f_array.shape)*1/det1intp[-1]
    det2convMask = np.ones(f_array.shape)*1/det2intp[-1]
    det1convMask[:j] = 1/det1intp
    det2convMask[:j] = 1/det2intp   
    det1convMask[-j:] = 1/np.flip(det1intp,0)
    det2convMask[-j:] = 1/np.flip(det2intp,0)
    

    ampA = np.fft.fft(A)
    ampB = np.fft.fft(B)
    outA = ampA*det1convMask
    outB = ampB*det2convMask
    AfreqCal = np.fft.ifft(outA)
    BfreqCal = np.fft.ifft(outB)

#==============================================================================
#     return AfreqCal,BfreqCal,t
#==============================================================================
    return AfreqCal.real,BfreqCal.real,t
    
    
    
    
    
    
    
    
if __name__ == '__main__':
    import numpy as np
    from matplotlib.pyplot import *
    
    t = np.linspace(0, 1e-3, 1e6)
    y = np.sin(50e9*2*np.pi*t**2)
    #y = np.sin(1e3*2*np.pi*t)
    A = y; B = y; Tinterval = t[1]
    Dict={'A':A,'B':B,'Tinterval':Tinterval}
    
    xx,yy,tt = cal_det_f2(Dict)
    
    plot(tt,yy.real)
#==============================================================================
#     psd(yy,Fs=1/t[1])
#==============================================================================
    show()
    
    
    
    
    
    
    
    
    
    
    