# -*- coding: utf-8 -*-
"""
Created on Wed Jan 16 12:44:24 2019
    Live updating picoscope trace.
@author: James
"""

import pyqtgraph as qt
import numpy as np
import picoscope_runner as pico

from pyqtgraph.Qt import QtGui, QtCore
from DAM import *

from pyqtgraph.dockarea import *
import pyqtgraph as pg
import sys
from numpy import *
from time import sleep


def testBasicPicoLiveFeed(ps):
    ''' Only works if 1 channel is used. '''
    settings = pico.setPicoTrace(ps,'A',1,1e-6,1e-3,res='12')
    ch = settings['Channel']
    ts = setttings['t_sample']
    t = np.arange(data.size)*ts
    data = pico.getPicoTraceV(ps,ch)
    
    
def senderPico(ps, ch, Vrange, t_sample, t_record, trig = 0, res = None):
    ''' Sets picoscope parameters and then sends traces to "Listener" '''
    import time
    ps = pico.open_pico()
    settings = pico.setPicoTrace(ps, ch, Vrange, t_sample, t_record, trig, res)
    
    
    ds = DAMSender()
    ch = settings['Channel']
    y = pico.getPicoTraceV(ps,ch)
    x= np.arange(y.size)*settings['Tsample']
    while 1:
        y = pico.getPicoTraceV(ps,ch)
        ds.pubData("Picoscope live feed", x,y)
        ds.pubData("feed^2", x,y**2)
        sleep(0.1) 
           
    
    
def listener():
    ''' Gets picoscope data from senderPico '''
    #global app
    app = pg.QtGui.QApplication([])
    dam1 = DockAreaManager(name="Test")
    x=linspace(0,1,1000)
    damListener = DAMListener(dam=dam1)
    damListener.startUpdating(100)
    if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        print("Application bit")
        pg.QtGui.QApplication.instance().exec_()
    return damListener    
    
    
    


## Start Qt event loop unless running in interactive mode or using pyside.
# =============================================================================
# if __name__ == '__main__':
#     import sys
#     if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
#         QtGui.QApplication.instance().exec_()
# =============================================================================
