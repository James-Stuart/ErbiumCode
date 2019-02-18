import pylab as pl
import numpy as np
from numpy import pi
import rigolfg 
    
def makeFrequencyHops(freqList=[200,600,1000], durations=[0.5, 0.5, 0.5], sampRate=10e3 ):
	wvfms=[]
	for freq, tTot in zip(freqList, durations):
	    t=np.arange(0,tTot, 1/sampRate);
	    wvfms.append(np.sin(2*pi*freq*t))
	return np.hstack(wvfms)


if __name__=="__main__":
	arr=makeFrequencyHops()