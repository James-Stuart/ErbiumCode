############BASIC FUNCTIONS OF THE RIGOL DM3068 DIGITAL MULTIMETER##############
###########################MILOS RANCIC 2014####################################


#import sys
import numpy as np
#from ctypes import *
from time import clock,sleep
from visa import ResourceManager
import datetime
#from struct import *
rm = ResourceManager()

def Initialise_DMM():
    
    #This creates the intrument handle for the Rigol Digital multimeter
    Rigol_DMM = rm.open_resource(u'USB0::0x1AB1::0x0C94::DM3O193300630::INSTR', timeout = 3000)
##     Rigol_DMM = instrument("GPIB::7::INSTR",  term_chars = '\n')
    #Rigol_DMM = instrument("GPIB0::7::INSTR", term_chars = '\n')
    #ask the multimeter for its name
    print ""
    print "-you are using the: " + Rigol_DMM.ask("*IDN?")
    
    #sets up the rigol to measure resistance with 200 KOhm range (range: 3)
    Rigol_DMM.write(":MEAS:RES 3")
    
    
    #generates a boolean to say that its been initialised
    rigol_bool = 1
    
    return(Rigol_DMM, rigol_bool)
    


def Rigol_DMM_Measure_Resistance(Rigol_DMM):
    
    Resistance = Rigol_DMM.ask(":MEAS:RES?")
    #convert the resistance string to a floating point and divide by 1000
##     Resistance = round(float(Resistance)/1000,2)
    Resistance = float(Resistance)
    
    #calculates the temperature based on the thermistor calibration 
    #(see page 62 of log book 2)
    z = (Resistance - 66)/22
    Temp = 0.016*z**4 - 0.03*z**3 - 0.0046*z**2 - 0.2*z + 1.7
    Temp = round(Temp, 2)
    
    #print 'resistance is: '  + str(Resistance)  + ' kOhms, temp is: ' + str(Temp) + ' K' 
    return(Resistance, Temp)


def Delete_After_use(Rrange=''):
    Rigol_DMM,bool=Initialise_DMM()
    
    if Rrange =='':
        RigolRange = 6
    else:
        RigolRange = Rrange
    for i in range(5000):
        
        
        r = Rigol_DMM.write("MEAS:RES " + str(RigolRange)) 
        r = Rigol_DMM.query("MEAS:RES?")
        r= float(r)
        
        if Rrange == '':
            if r >= 10e6:
                RigolRange = 6
            elif r >= 1e6 and r < 10e6:
                RigolRange = 5
            elif r >= 200e3 and r < 1e6:
                RigolRange = 4
            elif r >= 20e3 and r < 200e3:
                RigolRange = 3
            elif r >= 2e3 and r < 20e3:
                RigolRange = 2
            elif r >= 200 and r < 2e3:
                RigolRange = 1
            else:
                RigolRange = 0
            
        sleep(3)
        print(r)
        
def Rigol_Query_R_simple(Rigol_DMM):
    RigolRange = 4
    r = Rigol_DMM.write("MEAS:RES " + str(RigolRange)) 
    r = Rigol_DMM.query("MEAS:RES?")
    r = float(r)
    
    return r
    
    
def Rigol_Query_Resistance(Rigol_DMM,n=1,t=1):
    range = 6
    r = Rigol_DMM.write("MEAS:RES " + str(range)) 
    r = Rigol_DMM.query("MEAS:RES?")
    r= float(r)
    
    if r > 100e6:
        print('Warning: resistance measurement exceeds 100 Mega Ohms')
    rList = []
    time = []
    count = 0
    
    while n >0:
        count +=1
        #Find Resistance range
        if r >= 10e6:
            range = 6
        elif r >= 1e6 and r < 10e6:
            range = 5
        elif r >= 200e3 and r < 1e6:
            range = 4
        elif r >= 20e3 and r < 200e3:
            range = 3
        elif r >= 2e3 and r < 20e3:
            range = 2
        elif r >= 200 and r < 2e3:
            range = 1
        else:
            range = 0
        
        #Query for resistance in appropriate range
        r = Rigol_DMM.write("MEAS:RES " +str(range))
        r = Rigol_DMM.query("MEAS:RES?")
        timeNow = datetime.datetime.now()
        timeDiff = timeNow
        r = float(r)
        rList.append(r)   
        time.append(timeDiff) 
        sleep(t)
        n-=1
        
        if count == 10:
            count = 0
            print('Resistance is: ', r)
            print(n, ' Loops remaining.')
        
    rList = np.asarray(rList)
    
    np.save('C:\Users\Milos\Desktop\James\RigolResistance',np.hstack([time,rList]))
    return rList,time



def Res2Temp(r):
    '''Converts resistance to temperature for the room temp thermistor on smaple stick '''
    a=3.35e-3; b=2.56e-4; c=2.09e-6; d=7.30e-8
    Rr = r/1e4
    t = 1./(a + b*np.log(Rr) + c*np.log(Rr)**2 + d*np.log(Rr)**3) - 273.15
    return t
#Rigol_DMM = Initialise_DMM()
#Rigol_DMM_Measure_Resistance(Rigol_DMM)

if __name__ == '__main__':
    Rigol,bool = Initialise_DMM()
    R,time = Rigol_Query_Resistance(Rigol,10,1)
##     R,T = Rigol_DMM_Measure_Resistance(Rigol)
    print(R)
    print(time)
    
    import matplotlib.pyplot as plt
    plt.plot(time,R)
    plt.show()
##     print(T)