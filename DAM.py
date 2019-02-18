
import numpy as np
import zmq
import pickle

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

        #Save area
        saveDock=Dock("saveArea", size=(10,10))
        w1 = pg.LayoutWidget()
        label = pg.QtGui.QLabel("""Save/restore state""")
        saveBtn = pg.QtGui.QPushButton('Save state')
        restoreBtn = pg.QtGui.QPushButton('Restore state')
        restoreBtn.setEnabled(False)
        w1.addWidget(label, row=0, col=0)
        w1.addWidget(saveBtn, row=1, col=0)
        w1.addWidget(restoreBtn, row=2, col=0)
        saveDock.addWidget(w1)
        saveBtn.clicked.connect(self.save)
        restoreBtn.clicked.connect(self.load)
        self.saveBtn=saveBtn
        self.restoreBtn=restoreBtn
        self.area.addDock(saveDock)
        self.win.show()

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
        w.plot(x, y)
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



class DAMSender(object):
    def __init__(self, pubName=b"test"):
        self.sock= zmq.Context().socket(zmq.PUB)
        self.sock.set_hwm(10)
        self.sock.bind("tcp://*:%i" % PORT)
        self.pubName = pubName

    def pubData(self, name, x,y):
        msg = b'%s '%self.pubName + pickle.dumps({name: (x,y)})
        self.sock.send(msg)
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
        #TODO:
        #I should make scripts that either run testListener to get the live
        #feed data from the picoscope, or I need to make a listener for each
        #script that I want to read from the picoscope (I dont want to do this).
        
        #One way would be to give listener a variable which tells it which script
        #to run the data through, and just plots the output of the script.
        
        
        global app
        app = pg.QtGui.QApplication([])
        dam1 = DockAreaManager(name="Test")
        x=linspace(0,1,1000)
        damListener = DAMListener(dam=dam1)
        damListener.startUpdating(50)
        if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
            print("Application bit")
            pg.QtGui.QApplication.instance().exec_()
        return damListener
    
    
    def testPicoListener():
        pass
    

    def testSender():
        import time
        ds = DAMSender()
        x= linspace(0,1,1000)
        while 1:
            t = time.time()
            y = sin(2*pi*x+ t/10.) + 0.4*np.random.normal(size=x.size)
            ds.pubData("Noisy sin", x,y)
            ds.pubData("Noisy sin^2", x,y**2)
            sleep(0.1)
            
            
    def testPicoSender():
        import time
        import picoscope_runner as pico
        ps = pico.open_pico()
        settings = pico.setPicoTrace(ps, 'A', 1, 1e-6, 1e-3,res='12')
        
        
        ds = DAMSender()
        ch = settings['Channel']
        y = pico.getPicoTraceV(ps,ch)
        x= np.arange(y.size)*settings['Tsample']
        while 1:
            y = pico.getPicoTraceV(ps,ch)
            ds.pubData("Picoscope live feed", x,y)
            ds.pubData("feed^2", x,y**2)
            sleep(0.1) 
            
        ps.close()
        #TODO: All I need is the sender to send the basic live feed
        #TODO: Should also stress test this to see if it can handle sending Mega samples
        
