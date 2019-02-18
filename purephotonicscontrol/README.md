Wrapper Matt Berrington made for the PurePhotonics Laser.

Check out EXAMPLE.py for how to use it. It should be pretty simple.

Below are laser control functions I've implemented include.

Common functions:

ProbeLaser()					#Check's to see it laser it behaving. Will cycle the laser if it's not. If all is good, nothing is done
SetWavelength(wavelength) 		#Specify wavelength in nm. Note the wavelength will the rounded to the nearest 0.1GHz
SetFrequency(freq)				#Specify frequency in THz, accurate to 0.1GHz
SetPower(power)					#Specify power in dBm
EnableLaser(state)				#Turn laser on/off using 'True'/'False'
WaitForLaser()					#Wait until the laser is no longer pending and gives the thumbs up for the next command. I automatically do this after enabling 
EnableWhisperMode(state)		#Turn whisper mode on/off using 'True'/'False'

Sweeping functions:
		
SetSweepRange(range)			#Specify sweep range in GHz. Sweeping needs to be off when this is done
SetSweepRate(rate)				#Specify sweep range in MHz/s. Sweeping needs to be off when this is done
EnableSweep(state)				#Turn sweeping on/off using 'True'/'False'
ReadOffsetFreq()				#Returns the current frequnecy offset of the sweep in GHz. Can be buggy if you don't have a small delay between starting sweep and using this function
		
Jumping functions (not thoroughly tested, use at own risk):

SetNextFrequency(freq)			#Set frequency to jump to next
SetNextSled(sled)				#Set sled for next jump, which is found in laser calibration stuff
SetNextCurrent(current)			#Set current for next jump, which is found in laser calibration stuff
ExecuteJump()					#Jump!
FineTuneFrequency(ftf)

Other:
ReadTemp() 						#Return the laser temperature
ReadDeviceTemp(self)			#This returns the 'device temperature' instead of the 'laser temperature'. I'm unsure what the difference is
ReadDeviceCurrent(self):		#Return the device's current