# -*- coding: utf-8 -*-
"""
Created on Tue Jan  9 09:35:43 2018
Testing the recovery time when switching the JDSU EOM bias voltages. 
@author: James
"""

import Holeburn_james_wf3 as h
from HP8560E_Spectrum_Analyser import *
from time import sleep
import pulse_blaster as pb
import spectrum_image_HP8560E as SIH

s = 1
ms = 1e-3
us = 1e-6
ns = 1e-9

[SpecAn, SpecAn_Bool] = Initialise_HP8560E_SpecAn()

def EOM_test(SpecAn):
##     SpecAn.write('LG 10')
##     pb.Sequence([(['ch2'], 1*ms)], loop=False)
##     sleep(3)
##     SpecAn.write('MKPK HI')
##     num = SpecAn.query('MKA?')
##     print num
    
    pb.Sequence([(['ch2','ch5'], 1*ms)], loop=False)
    sleep(3)
    SpecAn.write("LG 2")
    h.run_offset(SpecAn, sweep = 2)
    SpecAn.write('ST 2')
    filepath = h.create_file(SpecAn, filename = 'EOM bias test', compensated = 'Y', n=1, burn_time = 0)
    pb.Sequence([(['ch1'],4*s)] + [(['ch2','ch4','ch5'], 3000*ms)] + [(['ch2','ch5'],1*s)],loop=False)
    filepath = h.record_trace(SpecAn, filepath, compensated = 'Y', n=1, burn_time = 0)
    
def view():
##     pb.Sequence([(['ch2','ch5'], 1*ms)], loop=False)
    pb.Sequence([(['ch2'], 1*ms)], loop=False)
    SpecAn.write('LG 10')
    SIH.free_run_plot_window('N',full_span = 'Y')
    
if __name__ == "__main__":
    EOM_test(SpecAn)
##     view()