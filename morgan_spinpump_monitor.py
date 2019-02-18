
from pylab import *
from HP8560E_Spectrum_Analyser import *
import pulse_blaster as pb

Hz = 1
kHz = 10**3
MHz = 10**6
GHz = 10**9

hr = 3600
mn = 60
s = 1
ms = 10**-3
us = 10**-6
ns = 10**-9

[SpecAn, SpecAn_Bool] = Initialise_HP8560E_SpecAn()


def pumpOnce(pumpTime=108s):
        pb.mems_switch_toggle(pumpTime,n=1,other_ch='',init_state = 1)
        sleep(spintime)
        pb.mems_switch_toggle(10*ms,n=1,other_ch='',init_state = 2)
        sleep(0.1)


def getModulationSpectrum():
	array = [(['ch2','ch5'], 0.5*s),(['ch2','ch5'], 0.1)] + [(['ch2','ch5'], 500*ms), (['ch2','ch4','ch5'], 350*ms)] + [(['ch2','ch5'], 100*ms)]
    pb.Sequence(array,loop=False)
