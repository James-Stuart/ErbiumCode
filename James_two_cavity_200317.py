import spectrum_image_HP8560E_james as S
import Tektronix_TDS220 as T
import pulse_blaster_Milos as pb
import os
import time

s = 1
ms = 10**-3
us = 10**-6
ns = 10**-9

#Setting up the Spectrum Analyser
S.SpecAn.write("SP 2MHz")
time.sleep(1)
S.move_center(0,True)


#Setting up the Tektronix
tek = T.Initialise_Tektronix_220()
tek.write("HOR:SCA 10e-3")
tek.write("HOR:POS 0")
tek.write("CH1:SCA 1")
tek.write("CH1:POS 0")

time.sleep(1)

S.SpecAn.write("SP 0")
S.SpecAn.write("SP?")
span_check = S.SpecAn.read()
print("Span is {}".format(span_check))



#Record oscilloscope data
tek.write("CH1:SCA?")
scale = float(tek.read())
tek.write("CH1:POS?")
divisions = float(tek.read())
voltage = scale*divisions


filename = 'C:\Users\Milos\Desktop\James\\laser_error_signal.txt'
try:
    os.remove(filename)
except OSError:
    pass
file = open(filename,'w')

tek.write('CH1:SCA?')
volt = tek.read()
tek.write('HOR:SCA?')
time = tek.read()

file.write('Scope is 10 div high, 10 div wide\n')
file.write('every data set is 2500 data points long')
file.write('Voltage scale\n')
file.write(str(volt) + '\n')
file.write('Time scale\n')
file.write(str(time) + '\n')
file.write('offset is ' + str(voltage))

for j in range(1):
    data = T.collect_scope_trace(tek)
    for i in range(len(data)):
        file.write(str(data[i])+"\n")
    

file.close


