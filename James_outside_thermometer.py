## Runs thermometer box JS1
## Thermiristor in series with resistor measures voltage drop, resistance over time.
## Voltages are read over the Tektronics TDS 220 oscilloscope.

## IMPORTANT set measurement 1,2,3,4 to CH1 mean, CH2 mean, CH2 p2p, CH1 p2p
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


data_points = 48*hour
count = 100


tek = T.Initialise_Tektronix_220()
## Channel 1 contains low voltage, channel 2 high (~18 V)
tek.write("CH1:SCA 0.5")
tek.write("CH1:POS -18")

tek.write("CH2:SCA 0.5")
tek.write("CH2:POS -36")



filename2 = 'C:\Users\Milos\Desktop\James\\lab_ambient_temp.txt'
try:
    os.remove(filename2)
except OSError:
    pass
file2 = open(filename2,'w')
file2.write('Voltage readings from \n input(total) voltage, thermristor voltage \n')


for i in range(data_points):
    tek.write("MEASU:MEAS1:VAL?")
    CH1_mean = tek.read()
    CH1_mean = float(CH1_mean[0:6])*10**int(CH1_mean[-2:-1])

    tek.write("MEASU:MEAS2:VAL?")
    CH2_mean = tek.read()
    CH2_mean = float(CH2_mean[0:6])*10**int(CH2_mean[-2:-1])

    tek.write("MEASU:MEAS3:VAL?")
    CH2_p2p = tek.read()
    CH2_p2p = float(CH2_p2p[0:6])*10**int(CH2_p2p[-3:-1])

    tek.write("MEASU:MEAS4:VAL?")
    CH1_p2p = tek.read()
    CH1_p2p = float(CH1_p2p[0:6])*10**int(CH1_p2p[-3:-1])
    
    file2.write("{0:.4f}, {1:.4f}, {2:.4f}, {3:.4f} \n".format(CH1_mean,CH2_mean))
    
    if count == 100:
        count = 0
        text = " Loop number {0:.0f} out of {1:.0f} \n".format(i,data_points)
        print text
    else:
        count = count+1
    
    time.sleep(1)
print count
