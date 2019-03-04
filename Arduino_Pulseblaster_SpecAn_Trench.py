from numpy import *
from ctypes import *
from visa import *
from struct import *
import os
import subprocess
rm = ResourceManager()

def Initialise_Arduino(com_port):
    
    #initialises the arduino board, which causes the arduino to reset
    #we then wait 3 seconds for the arduino to reset correctly
    Arduino = rm.open_resource(com_port, write_termination = '', timeout = 15000)
    
    print 'you are using the arduino pulseblaster!'
    return(Arduino)
#


def Upload_Arduino(program_name):
    out = subprocess.call([r"C:\\Users\Milos\\Desktop\\Arduino-1.5.2\\arduino", "--upload", r"C:\\Users\\Milos\Desktop\\Er_Experiment_Interface_Code\\" + program_name + "\\" + program_name + ".ino"])

#this function generates an arduino .ino script with 'delay' ms of delay between burning a spectral hole and sweeping with the SpecAn


def Edit_Pulse_Sequence(delay,program_name):
    
        # Read in old script
	f = open("C:\\Users\\Milos\Desktop\\Er_Experiment_Interface_Code\\" + program_name + "\\" + program_name + ".ino", 'r')
        script = f.read()
        f.close()

        #repeat the same thing for the serial print line
	m = re.search("the following prints the delay time via the serial port to verify correct pulse sequence execution:", script)
        A = m.end()
	m = re.search("println followup marker", script)
	B = m.start()

	#define first section of the new script: everything upto the time delay
	script1 = script[0:A+1]
        
        #replace the delay time in the serial print line
        script2 = "Serial.println(\"" + str(delay) +  " ms delay pulse program\"" + ");\n//";
		
       
        
        # Replace time delay by finding the text above and below the line of code
	m = re.search("input delay time:", script)
        C = m.end()
	m = re.search("delay followup marker", script)
	D = m.start()

        #write the middle bit of the script
        script3 = script[B:C+1]
        
        #Write new time delay, which also creates a new line (/n) and then ensures that the follow-up
        #statement is a comment (//) as the re.search function cuts out the // from the original string
	script4 = r"delay("+str(int(delay)) + ");\n//"
        
        #write  the last section of the script
        script5 = script[D:len(script)]
        
        #Put all the bits together
	script_out = script1+script2+script3+script4+script5
        
	
	# Rewrite the ino file
	f = open("C:\\Users\\Milos\Desktop\\Er_Experiment_Interface_Code\\" + program_name + "\\" + program_name + ".ino", 'w')
	f.write("%s"%script_out)
	f.close()
        
   



