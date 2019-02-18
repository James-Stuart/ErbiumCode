#Is the LASER locked.exe
#Looks at (and records) 4 voltage readings from a TDS220 oscilloscope to record how well (/if) the laser is locked
#CH1: Output from the cavity transmission
#CH2: Output from the Slow AMP

import Tektronix_TDS220 as T
import os
import time
import datetime

hour = 3600
min = 60
s = 1
ms = 10**-3
us = 10**-6
ns = 10**-9

expermient_time = 16*hour#Data recording time
acquisition_frequency = 1*s #Time between data point
n = expermient_time/acquisition_frequency #Number of data points

ts = time.time()
date = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S') #Time of experiment start.

count = 99

#Sets up a file and writes header
filename = 'C:\Users\Milos\Desktop\James\\17-05-30_laser_lock.txt'
try:
    os.remove(filename)
except OSError:
    pass
file = open(filename,'w')
file.write('Date: ' + date + '\n')
file.write('Data recordings over laser locking \n')
file.write('Cavity transmission, cavity transmission variance, slow amp output, slow amp output variance \n')

tek = T.Initialise_Tektronix_220() #initialise the scope
tek.write("CH1:SCA 0.05") #Set initial parameters
tek.write("CH1:POS 0")
tek.write("CH2:SCA 5")
tek.write("CH2:POS 0")
tek.write("HOR:SCA 0.001")

for i in range(n):
    count +=1    
    tek.write("MEASU:MEAS1:VAL?")
    CH1_mean = T.num_convert(tek.read()) #num_convert converts tek output to standard foat

    tek.write("MEASU:MEAS2:VAL?")
    CH2_mean = T.num_convert(tek.read())

    tek.write("MEASU:MEAS3:VAL?")
    CH2_p2p = T.num_convert(tek.read())

    tek.write("MEASU:MEAS4:VAL?")
    CH1_p2p = T.num_convert(tek.read())
    
    time_data = time.time() #Takes time of each data point
    data_time = datetime.datetime.fromtimestamp(time_data).strftime('%H:%M:%S')
    
    file.write("{0:.4f}, {1:.4f}, {2:.4f}, {3:.4f}, {4:s}\n".format(CH1_mean, CH1_p2p, CH2_mean, CH2_p2p, data_time))
    
    if count == 100:
        count = 0
        print("Loop " + str(i) + " out of " + str(n) + "\n")
        
    time.sleep(0.2)
        
file.close()