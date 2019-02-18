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
length_of_experiment = 0.5*hour #How long the recording will go for
time_between_recordings = (1) #Time between data points in seconds
if time_between_recordings < 0.18:
    raise RuntimeError, "Set time to > 0.18s"
    
n = int(length_of_experiment/(time_between_recordings)) #Sets the amount of loops

#Records the start time of the script
ts = time.time()
time_experiment_started = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
count = 99 #used for printing out which loop you're at



## #Initials and set up parameters for oscilloscope
## tek = T.Initialise_Tektronix_220()
## #Channel 1 contains low voltage, channel 2 high (~18 V)
## tek.write("CH1:SCA 0.5")
## tek.write("CH1:POS -18")
## tek.write("CH2:SCA 0.5")
## tek.write("CH2:POS -36")
## #Sets up file for oscilloscope data
## filename2 = 'C:\Users\Milos\Desktop\James\\17-05-19 test lab_ambient_temp_2ndrun.txt'
## try:
##     os.remove(filename2)
## except OSError:
##     pass
## file2 = open(filename2,'w')
## file2.write('Voltage readings from \n input(total) voltage, thermristor voltage \n')

#Sets up a file for the spectrum analyserp
filename = 'C:\Users\Milos\Desktop\James\\18-03-21 half hour cavity drift.txt'
try:
    os.remove(filename)
except OSError:
    pass
file = open(filename,'a')
file.write('Recording of cavity drift by measuring the frequency of the cavity bottom over time. \n')
file.write(time_experiment_started + '\n')
file.write('Frequency, Time \n')



file.close()

#Taking data
for i in range(n):
    #Controls the spec. analyser
    file = open(filename,'a')
    count += 1
    S.move_center(0,False) #moves spec. center to local minimum
    S.SpecAn.write("MKF?") #records locacl minimum
    data = (float(S.SpecAn.read()))
    
    time_data = time.time() #Takes time of each data point
    experiment_time = datetime.datetime.fromtimestamp(time_data).strftime('%Y-%m-%d %H:%M:%S')
    
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
    
    #Loop takes approx 0.16s 
    file.close()
    time.sleep(time_between_recordings - 0.177)
    


file.close()
## file2.close


print "Finished!"