
import numpy as np
import zmq
import pickle
from pyqtgraph.dockarea import *
import pyqtgraph as pg
import sys
from numpy import *
from time import sleep
import time

class DockAreaManager(object):
    """ A class to simply manage a pyqtgraph DockArea.
    Tha idea is that you make a DAM, feed it data, and it will do an 
    ok job of plotting that data and remembering your settings (chosen 
    by mouse clicks).
    Remembering settings is currently broken however.
    """
    win=None
    area=None
    dockD=None

    def __init__(self, name='Dock window'):
        self.name=name
        area=DockArea()
        win = pg.QtGui.QMainWindow()
        win.setCentralWidget(area)
        win.resize(400,300)
        win.setWindowTitle(name)
        self.area=area
        self.dockD={}
        self.win=win
        self.isPaused = False #By default the updating is not paused 

        #Save area
        saveDock=Dock("saveArea", size=(10,10))
        w1 = pg.LayoutWidget()
        label = pg.QtGui.QLabel("""Save/restore state""")
        saveBtn = pg.QtGui.QPushButton('Save state')
        restoreBtn = pg.QtGui.QPushButton('Restore state')
        restoreBtn.setEnabled(False)
#==============================================================================
#         pauseBtn = pg.QtGui.QPushButton('Pause graph') #pauseBtn
#==============================================================================
        w1.addWidget(label, row=0, col=0)
        w1.addWidget(saveBtn, row=1, col=0)
        w1.addWidget(restoreBtn, row=2, col=0)
#==============================================================================
#         w1.addWidget(pauseBtn, row=3, col=0) #pauseBtn
#==============================================================================
        saveDock.addWidget(w1)
        saveBtn.clicked.connect(self.save)
        restoreBtn.clicked.connect(self.load)
#==============================================================================
#         pauseBtn.clicked.connect(self.pause) #pauseBtn
#==============================================================================
        self.saveBtn=saveBtn
        self.restoreBtn=restoreBtn
        self.area.addDock(saveDock)
        self.win.show()
        
    def pause(self):
        ''' A button toggles if the graph is updating. '''
        self.isPaused = (self.isPaused+1)%2 #flip the bool


    def save(self):
        self.state = self.area.saveState()
        pickle.dump(self.state, open("dockManager_{}_{}.pkl".format(__name__, self.name), 'wb') )
        self.restoreBtn.setEnabled(True)
    def load(self):
        try:
            if self.state is None:
                state=pickle.load(open("dockManager_{}_{}.pkl".format(__name__, self.name), 'rb') )
                state={k:v for k,v in state if k in self.dockD.keys()} 
            self.area.restoreState(self.state)
        except Exception as e:
            print(e.args[0])

    def addDockPlot(self, name, x=None,y=None, title=None, **kwargs):
        dock=Dock(name, size=(200, 200))
        if title is None:
            title=name
        w = pg.PlotWidget(title=title)
        if y is None and x is not None:
            y=x; x=None
        if x is None:
            x=arange(y.size)
        
        #If plots are too big plot downsampled array
        if y.size < 1000000:
            w.plot(x, y)
        else:
            x.plot(x[0:-1:1000],y[0:-1:1000])
            
            
        dock.addWidget(w);
        self.dockD[name]=dock
        self.area.addDock(dock)
    def getPlotItem(self, name):
        return self.dockD[name].findChild(pg.PlotWidget).plotItem

    def setData(self, name, x,y=None):
        if y is None:
            y=x; x=np.arange(y.size)
        self.getPlotItem(name).curves[0].setData(x,y)
    def updateFromDict(self, D):
        """ Update/create plots from the dictionary D containing curves to be plotted
        """
        if self.isPaused:
            pass
        else:
            for key, val in D.items():
                if len(val)>2:
                    val=(val,)
                if key in self.dockD:
                    self.setData(key, *val)
                else:
                    self.addDockPlot(key, *val)

PORT = 5561
class DAMListener(object):
    """A simple way of updating a DAM from other processes. Use DAMSender
    from other processes to send data here."""
    timer = None
    def __init__(self, subName=b"test", dam=None):
        self.sock= zmq.Context().socket(zmq.SUB)
        self.sock.set_hwm(10)
        self.sock.connect("tcp://localhost:%s" % PORT)
        self.sock.setsockopt(zmq.SUBSCRIBE, b"%s" % subName)
        if dam is None:
            dam =DockAreaManager(name="Default")
        self.dam = dam
        if 0:
            rawPltL=[]
            for col in range(3):
                for row in range(3):
                    rawPltL.append(gwRaw.addPlot(col=col, row=row))
            self.rawPltL=rawPltL
            subPltL=[]
            for col in range(2):
                for row in range(2):
                    subPltL.append(gwRaw.addPlot(col=col, row=row))
            self.gwRaw=gwRaw
            self.gwSub=gwSub

    def update(self):
        if self.sock.poll(10):
            topic,msg= self.sock.recv().split(b' ', 1)
            D = pickle.loads(msg)
            self.dam.updateFromDict(D)
            #print("{} updated".format(topic))
        else:
            print("Nothing recieved")
            return None

    def startUpdating(self, interval):
        self.timer = pg.QtCore.QTimer()
        self.timer.timeout.connect(self.update)
        self.timer.start(interval)
    
    def stop(self):
        self.timer.stop()

    def close(self):
        self.sock.close()
        if self.timer:
            timer.stop()

class DAMListenerPico(object):
    """A simple way of updating a DAM from other processes. Use DAMSender
    from other processes to send data here."""
    timer = None
    analysis = ""
    dam = ""
    def __init__(self, subName=b"test", dam=None):
        self.sock= zmq.Context().socket(zmq.SUB)
        self.sock.set_hwm(10)
        self.sock.connect("tcp://localhost:%s" % PORT)
        self.sock.setsockopt(zmq.SUBSCRIBE, b"%s" % subName)
        if dam is None:
            dam =DockAreaManager(name="Default")
        self.dam = dam
        self.analysis =""
        if 0:
            rawPltL=[]
            for col in range(3):
                for row in range(3):
                    rawPltL.append(gwRaw.addPlot(col=col, row=row))
            self.rawPltL=rawPltL
            subPltL=[]
            for col in range(2):
                for row in range(2):
                    subPltL.append(gwRaw.addPlot(col=col, row=row))
            self.gwRaw=gwRaw
            self.gwSub=gwSub

    def update(self):#, analysis = ''):
        '''Loads the message from sender, reads it in a certain format {'t','A','B'} 
        (A or B might be None). Analyses the data, ChA and ChB. And then makes
        a new dictionary {'Channel A':[t,A],'Channel B':[t,B]}.
        
        This way is slightly inefficient but follows the original format that
        DAMListener uses.'''
        if self.sock.poll(10):
            topic,msg= self.sock.recv().split(b' ', 1)
            D = pickle.loads(msg)
            
            t= D['t']
            DictAnalysed = {}

            for string in ['A','B']:
            
                if D[string] is not None:
                    data = D[string]
                    
                    #If data is a bulk block (multiple traces), only look and plot 
                    #the first trace
                    if data.ndim > 1:
                        data = data[0]
                    t2,aData = self.analyseData(t,data) 
                    
                    DictAnalysed['Channel ' + string] = t2,aData
                
            self.dam.updateFromDict(DictAnalysed)
            #print("{} updated".format(topic))
        else:
            print("|",end='')
            return None
        
    
    def analyseData(self, t, data):
        if self.analysis in ['','raw']:
            aData = data
        elif self.analysis == 'square':
            aData = data**2
        elif self.analysis in ['FFT','fft']:
            aData = abs(np.fft.fft(data))**2
            #'t' is now frequency
            t = np.fft.fftfreq(data.shape[0], t[1]-t[0])
            
            #Only interested in positive frequencies
            aData = aData[:int(np.floor(len(aData)/2))]
            t = t[:len(aData)]
        else:
            print('Analysis type not recognised')
        return t,aData
    

    def startUpdating(self, interval):#, analysis = ''):
        self.timer = pg.QtCore.QTimer()
        self.timer.timeout.connect(self.update)
        self.timer.start(interval)
    
    def stop(self):
        self.timer.stop()

    def close(self):
        self.sock.close()
        if self.timer:
            timer.stop()

class DAMSender(object):
    def __init__(self, pubName=b"test"):
        self.sock= zmq.Context().socket(zmq.PUB)
        self.sock.set_hwm(10)
        self.sock.bind("tcp://*:%i" % PORT)
        self.pubName = pubName

    def pubData(self, name, x,y):
        msg = b'%s '%self.pubName + pickle.dumps({name: (x,y)})
        self.sock.send(msg)
        
    def pubDict(self, Dict):
        ''' Pickle Pico .mat  dictonary and send'''
        msg =  b'%s '%self.pubName + pickle.dumps(Dict)
        self.sock.send(msg)
        
    def close(self):
        '''Closes the port (ZMQ)'''
        self.sock.close()
        
        
if __name__=="__main__":
    # TESTING: In one process (probably IPython, with command line argument '--gui=qt5'), run "testListener()". In another, run "testSender()"


    from pyqtgraph.dockarea import *
    import pyqtgraph as pg
    import sys
    from numpy import *
    from time import sleep
    #app=pg.mkQApp()
    app=None
    def testListener():
        global app
        app = pg.QtGui.QApplication([])
        dam1 = DockAreaManager(name="Test")
        x=linspace(0,1,1000)
        damListener = DAMListener(dam=dam1)
        damListener.startUpdating(90)
        if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
            print("Application bit")
            pg.QtGui.QApplication.instance().exec_()
        return damListener
    
    
    def testListenerPico():
        global app
        app = pg.QtGui.QApplication([])
        dam1 = DockAreaManager(name="Test")
        damListener = DAMListenerPico(dam=dam1)
        damListener.startUpdating(90)#, analysis)
        if 0:#(sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION') and 0:
            print("Application bit \n Nothing recieved:")
            pg.QtGui.QApplication.instance().exec_()
        return damListener

        
        
#==============================================================================
#     def testSenderPico():
#         ''' This is meant to imitate testSender, but have the message in a 
#         .mat Picoscope style dictionary '''
#         ds = DAMSender()
#         x= np.linspace(0,1,1000)
#         
#         try:
#             while 1:
#                 #Get picoscope trace, make Dictionary with t,A,B arrays  
#                 
#                 tt = time.time()
#                 tInterval = 1 
#                 if 'tStart' not in locals():
#                     tStart=0
#                 A = np.sin(200*np.pi*x+ tt/10.) + 0.4*np.random.normal(size=x.size)
#                 
#                 #I dont like this...
#                 if 'A' not in locals():
#                     A = None
#                     t = np.arange(tStart,B.shape[0])*tInterval
#                         
#                 if 'B' not in locals():
#                     B = None
#                     t = np.arange(tStart,A.shape[0])*tInterval
#                     
#                 testDict = {'t':t, 'A':A, 'B':B}
#                 
#                 ds.pubDict(testDict)
#                 sleep(0.1)
#         except KeyboardInterrupt():
#             pass
#         finally:
#             ds.close()
#==============================================================================
            
    def testSenderPico():
        ''' This is meant to imitate testSender, but have the message in a 
        .mat Picoscope style dictionary '''
        ds = DAMSender()
        x= np.linspace(0,1,1000)
        
        try:
            while 1:
                #Get picoscope trace, make Dictionary with t,A,B arrays  
                
                ###############################################################
                #Making a fake picoscope trace
                tt = time.time()
                A = 2**15*(np.sin(200*np.pi*x+ tt/10.) + 0.4*np.random.normal(size=x.size))
                picoData = {'A':A, 'RangeA': 1.0, 'Resolution': 16, 'Tsample':1e-3, 'tStart':tt}
                ###############################################################
                
                if 'A' not in picoData:
                    A = None
                else:
                    A = picoData['A']
                    RangeA = picoData['RangeA']
                    t = np.arange(A.shape[0])*picoData['Tsample']
                    
                    #Convert picoData to voltages
                    A *= 1/(2**(picoData['Resolution']-1))*RangeA
                    
                if 'B' not in picoData:
                    B = None
                else:
                    B = picoData['B']
                    RangeB = picoData['RangeB']
                    t = np.arange(B.shape[0])*picoData['Tsample']                  
                    
                    #Convert picoData to voltages
                    B *= 1/(2**(picoData['Resolution']-1))*RangeB
                

                testDict = {'t':t, 'A':A, 'B':B}#, 'tStart':picoData['tStart']}
                
                ds.pubDict(testDict)
                sleep(0.1)
        except KeyboardInterrupt:
            pass
        finally:
            ds.close()
            
#TODO: testSenderPico, set it up to send A, B data (perhaps as two seperate Dict)
            #But I would prefer it as 1 Picoscope .mat style Dict
        
