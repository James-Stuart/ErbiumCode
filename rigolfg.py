##############################################################################
#          Morgan's code for a Rigol AWG, compatible with DG1022Z
##############################################################################

from time import sleep
#rom pylab import *
import pylab as pl
import time
from numpy import pi
import numpy as np
import pdb

import FG

class RigolFG(FG.FG):
    addr="USB0::0x1AB1::0x0642::DG1ZA193403359::INSTR"
    numChans=2 
    
    def chanStr(self, chanNum):
        return "" if chNum==0 else ":CH2"

    def configureHandle(self):
        self.handle.query_delay=0.5
        self.handle.timeout=20000
        normalWrite=self.handle.write
        def newWrite(*args, **kwargs):
            normalWrite(*args, **kwargs)
        self.handle.write=newWrite


    def setOutputState(self, bOn, chNum=0):
        headStr= "OUTPUT" if chNum==0 else "OUTPUT:CH2"
        stateStr= 'ON' if bOn else 'OFF'
        #sleep(0.5);
        out=self.handle.write("{} {}".format(headStr, stateStr));
        #sleep(0.5);
        return out

    @staticmethod
    def array_to_text_block(data, scl=True):
        """
        Takes a numpy array and converts it into a 16bit array in a string format
        """
        data=np.array(data,dtype='f8')
        if scl:
            lowV=data.min()
            highV=data.max()
            data=(data-lowV)/np.abs(highV-lowV)*2.-1.0
            #data/=abs(data).max()
            #data*=0.5#8191
        dataInt=np.rint((data+1)/2*(2**14-1)).astype('u2')
        #pl.plot(dataInt)
        #pl.show()
        #pdb.set_trace()
        datStr=','.join([str(num) for num in dataInt])
        print(datStr[:100])
        return datStr
    
    @staticmethod
    def array_to_binary_block(data, scl=True):
        ''' 
        Takes a numpy array and converts it into a 16bit array in str binary form.
        '''
        data=np.array(data)
        if scl:
            data/=abs(data).max()
            
        data=np.rint(data).astype('i2')
        dataBytes=bytes(data)
        N=len(dataBytes)
        Nstr=str(N)
        return ( "#{0}{1}".format(len(Nstr), Nstr),  dataBytes )
        #return "#{0}{1}{2}".format(len(Nstr), Nstr), data.tobytes())
    
    
    def uploadWaveform(self,y, scl=True, name="VOLATILE"):
        '''
            Converts numpy array "y" into a text block and uploads it to the
            Rigol onboard memory as VOLATILE.
        '''
        #datStr=self.__super__.array_to_text_block(y, 0, 16383, scl=scl)
        datStr=self.array_to_text_block(y, scl=scl)
        self.handle.write("DATA:DAC {},{}".format(name,datStr))
        

    def setOutputWaveForm(self, t, y):
        self.allOff()
        self.uploadWaveform(y)
        self.setPeriod((t[1]-t[0])*t.size)
        errStr=self.getErr()
        errVal=int(errStr.split(',')[0])
        #if errVal!= 0 and errVal != -221:
        if errVal:
            raise ValueError(errStr.split(',')[1])
        self.setLH(y.min(), y.max())
        self.curWaveform=y
        self.setOutputState(True, chNum=0)
        
        
    def uploadAndSetWaveform(self, t,x,chNum=0):
        """Simple upload a waveform and set it active.
        """
        figure()
        chanStr="" if chNum==0 else ":CH2"
        self.handle.write('FUNC:USER{} VOLATILE'.format(chanStr))
        
        x=np.array(x)
        T=max(t)-min(t)
        F=int(1./T)
        self.handle.write('FREQ{} {}'.format(chanStr, F))
        #sleep(0.4)
        #self.handle.write('VOLT:UNIT{} VPP'.format(chanStr))
        #sleep(0.4)
        lowV=x.min()
        highV=x.max()
        x=(x-lowV)/np.abs(highV-lowV)*1.9999-1.0

        if lowV <-5. or highV>5.:
            raise ValueError("Waveform must be between -5 and 5 V")
        self.handle.write('VOLT:LOW{} {:.3f}'.format(chanStr, lowV))
        #sleep(0.4)
        self.handle.write('VOLT:HIGH{} {:.3f}'.format(chanStr, highV))
        #sleep(0.4);
        
        if chNum==0:
            name= "CH1DEF" 
            #headStr= "FUNC:USER"
        elif chNum==1:
            name="CH2DEF"
            self.handle.write("FUNC:CH2 USER")
##             sleep(0.3);
            #headStr= "FUNC:USER:CH2"
        else:
            raise ValueError("Channel can be 0 or 1")
        
        catL=self.handle.query("DATA:CAT?").split(',')
        print(catL)
        while '"{}"'.format(name) in catL:
            self.handle.write("DATA:DEL {}".format(name) )
            sleep(0.2);
            catL=self.handle.query("DATA:CAT?").split(',')
            print("deleted 1");
        # This should be modified slightly, probably
        outForm=x*16383
        #datStr=','.join(['%i' % num for num in outForm])
        datStr=','.join(['{:.3f}'.format(num) for num in x])
        print(datStr[:100])
        #pdb.set_trace()
        #plot(x)
        print("write: {}".format( self.handle.write("DATA VOLATILE,{}".format(datStr))) )
        sleep(8.0);
        print("copy, {}".format(self.handle.write('DATA:COPY {}'.format(name))) )
        sleep(8.0);
        tStart=time.time()
        while not '"{}"'.format(name) in catL:
            sleep(0.3)
            catL=self.handle.query("DATA:CAT?").split(',')
            print(catL)
            if time.time()-tStart > 5: 
                raise TimeoutError("Timed out waiting for waveform to be uploaded")
        sleep(0.5)
        out=self.handle.write('FUNC:USER{} {}'.format(chanStr, name))
        sleep(0.4)
        print("func:user {}".format(out) );
        return out
        
    def setTriggerMode(self, mode="ext"):
        #allowed_modes=['int', 'ext', 'man']
        modeTransDict={'int':'IMM',
                'ext':'EXT',
                'man':'BUS'}
        if not modeTransDict.has_key(mode):
            raise ValueError('Trigger mode needs to be one of {}'.format(modeTransDict.keys()) )
        label=modeTransDict[mode]
        return self.handle.write("TRIG:SOUR {0}".format(label)) 
        
    def setTriggerDelay(self,delay):
        return self.handle.write('TRIG:DEL {}'.format(delay))

    def trigger(self):
        raise NotImplementedError('No software trigger available for the rigol1000')

    def setPeriod(self, T):
        self.handle.write('FREQ {:.5f}'.format(1./T))

    def setLowHigh(self, low, high):
        self.handle.write('VOLT:LOW {:.3f}'.format(low) )
        self.handle.write('VOLT:HIGH {:.3f}'.format(high) )

    def setOffset(self, offset):
        self.handle.write('VOLT:OFFS {:.3f}'.format(offset) )
    
    def setLoad(self, load=50, chNum=0):
        """ Set output impedance on the relevant channel
            If load is -ve, infinite is assumed
            If +ve then 50 is set.
        """
        chStr="" if chNum==0 else ":CH2"
        if load >0:
            loadStr="50"
        else:
            loadStr="INF"
        self.handle.write('OUTP:LOAD:{} {}'.format(chStr,loadStr) );

    def setInverted(self, bInvert=True):
        super().setInverted(bInvert)
        
        
if __name__=="__main__":
    
    fg=RigolFG();
    def sendPulse(tDelay=1, tWidth=1000, tTotal=4096):
        ''' 
        Uploads basic pulse to Rigol with three parameters tDelay, tWidth, tTotal
        tDelay: time before the pulse starts
        tWidth: width of the pulse
        tTotal: total time, units of all parameters are us.
        
        When setting width to 50us, pulse width is ~10us
        When setting width to 10us, pulse width is ~2.4us, but tTotal is unchanged 
        '''
    
        t=np.linspace(0,tTotal,tTotal*20)*1.0; #Sets time axis with 1/20us resolution
        y=np.where( (t>tDelay) & (t<tDelay+tWidth), 5.0, 0.) #Creates a square wave

        fg.setLoad(50,0) #Setting output impedance
        #from pylab import plot,show
        #plot(t,y)
        y=np.sin(2*pi*t)
        fg.uploadWaveform(y);
        fg.setPeriod(tTotal*1e-6);
        fg.setLowHigh(-5.,5.0) #Low voltage, high voltage
        print('Voltage offset: ' + fg.handle.query("VOLT:OFFS?"))
        fg.handle.write('OUTP on') #Turn channel 1 on
        pl.show()
        print('Size: {}'.format(t.size))

    #sendPulse(10.,100.,400)
    #fg.setTriggerDelay(200*1e-6)
    
