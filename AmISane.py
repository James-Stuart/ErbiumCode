## Move Spectrum analyser near to a canvity with a relevant span size, <10MHz
## Code will record the frequency of the bottom of the cavity in time intervals
## Also records voltages from an input and across a thermistor for ambient lab temp measurements
import spectrum_image_HP8560E_james as S
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
##================================== Experiment Length ==============================================
#Note the experiment will be aprox 10% longer than the set time, due to loops speeds
length_of_experiment = 15*hour #How long the recording will go for
time_between_recordings = (1) #Time between data points in seconds
n = int(length_of_experiment/(time_between_recordings)) #Sets the amount of loops

#Records the start time of the script
ts = time.time()
time_experiment_started = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
count = 99 #used for printing out which loop you're at

filename = 'C:\Users\Milos\Desktop\James\\18-03-07 cavity drift.txt'
try:
    os.remove(filename)
except OSError:
    pass
file = open(filename,'w')
file.write('Recording of cavity drift by measuring the frequency of the cavity bottom over time. \n')
file.write(time_experiment_started + '\n')
file.write('Frequency, Time \n')

#Taking data
for i in range(n):
    #Controls the spec. analyser
    count += 1
    S.move_center(0,False) #moves spec. center to local minimum
    S.SpecAn.write("MKF?") #records locacl minimum
    data = (float(S.SpecAn.read()))
    
    time_data = time.time() #Takes time of each data point
    experiment_time = datetime.datetime.fromtimestamp(time_data).strftime('%H:%M:%S')
    
    file.write("{0:.0f} , {1:s}\n".format(data, experiment_time))

##     #Takes data from the oscilloscope
##     tek.write("MEASU:MEAS1:VAL?")
##     CH1_mean = tek.read()
##     CH1_mean = float(CH1_mean[0:6])*10**int(CH1_mean[-2:-1])

##     tek.write("MEASU:MEAS2:VAL?")
##     CH2_mean = tek.read()
##     CH2_mean = float(CH2_mean[0:6])*10**int(CH2_mean[-2:-1]) 
##     file2.write("{0:.4f}, {1:.4f} \n".format(CH1_mean,CH2_mean))    
    
    if count == 100:
        print("Loop " + str(i) + " out of " + str(n) + "\n")
        count = 0
    
    time.sleep(time_between_recordings)
    


file.close()
## file2.close


print "Finished!"