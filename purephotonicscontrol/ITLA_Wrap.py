"""Wrap made by Matt Berrington, based off the CLI python file that Pure Photonics provides. Last updated 19th Feb 2018

To use this wrapper simply import it in your script that will execute the laser control. """

import serial
import time
import struct
import os
import os.path
import time
import sys
import threading
import math
import logging

ITLA_NOERROR=0x00
ITLA_EXERROR=0x01
ITLA_AEERROR=0x02
ITLA_CPERROR=0x03
ITLA_NRERROR=0x04
ITLA_CSERROR=0x05
ITLA_ERROR_SERPORT=0x01
ITLA_ERROR_SERBAUD=0x02

REG_Nop=0x00
REG_Mfgr=0x02
REG_Model=0x03
REG_Serial=0x04
REG_Release=0x06
REG_Gencfg=0x08
REG_AeaEar=0x0B
REG_Iocap=0x0D
REG_Ear=0x10
REG_Dlconfig=0x14
REG_Dlstatus=0x15
REG_Channel=0x30
REG_Power=0x31
REG_Resena=0x32
REG_Grid=0x34
REG_Fcf1=0x35
REG_Fcf2=0x36
REG_Oop=0x42
REG_Opsl=0x50
REG_Opsh=0x51
REG_Lfl1=0x52
REG_Lfl2=0x53
REG_Lfh1=0x54
REG_Lfh2=0x55
REG_Currents=0x57
REG_Temps=0x58
REG_Ftf=0x62
REG_Mode=0x90
REG_PW=0xE0
REG_Csweepsena=0xE5
REG_Csweepamp=0xE4
REG_Cscanamp=0xE4
REG_Cscanon=0xE5
REG_Csweepon=0xE5
REG_Csweepoffset=0xE6
REG_Cscanoffset=0xE6
REG_Cscansled=0xF0
REG_Cscanf1=0xF1
REG_Cscanf2=0xF2
#This registry is write only
REG_CjumpTHz=0xEA
#This registry is write only
REG_CjumpGHz=0xEB
#This registry is write only
REG_CjumpSled=0xEC
#This registry is write only
REG_CjumpCurrent=0xE9
#This registry is write only
REG_Cjumpon=0xED
REG_Cjumpoffset=0xE6

READ=0
WRITE=1
latestregister=0
tempport=0
raybin=0
queue=[]
maxrowticket=0

_error=ITLA_NOERROR
seriallock=0

class ITLA_Class:
	def __init__(self,port,baudrate):
            self.sercon = self.ITLAConnect(port,baudrate)

	def stripString(self,input):
		outp=''
		input=str(input)
		teller=0
		while teller<len(input) and ord(input[teller])>47:
			outp=outp+input[teller]
			teller=teller+1
		return(outp)

	def ITLALastError(self):
		return(_error)

	def SerialLock(self):
		global seriallock
		return seriallock

	def SerialLockSet(self):
		global seriallock
		global queue
		seriallock=1
    
	def SerialLockUnSet(self):
		global seriallock
		global queue
		seriallock=0
		queue.pop(0)
    
	def checksum(self,byte0,byte1,byte2,byte3):
		bip8=(byte0&0x0f)^byte1^byte2^byte3
		bip4=((bip8&0xf0)>>4)^(bip8&0x0f)
		return bip4
    
	def Send_command(self,sercon,byte0,byte1,byte2,byte3):
		sercon.write(chr(byte0))
		sercon.write(chr(byte1))
		sercon.write(chr(byte2))
		sercon.write(chr(byte3))

	def Receive_response(self,sercon):
		global _error,queue
		reftime=time.clock()
		while sercon.inWaiting()<4:
			if time.clock()>reftime+0.25:
				_error=ITLA_NRERROR
				return(0xFF,0xFF,0xFF,0xFF)
			time.sleep(0.0001)
		try:
			byte0=ord(sercon.read(1))
			byte1=ord(sercon.read(1))
			byte2=ord(sercon.read(1))
			byte3=ord(sercon.read(1))
		except:
			print 'problem with serial communication. queue[0] =',queue
			byte0=0xFF
			byte1=0xFF
			byte2=0xFF
			byte3=0xFF
		if self.checksum(byte0,byte1,byte2,byte3)==byte0>>4:
			_error=byte0&0x03
			return(byte0,byte1,byte2,byte3)
		else:
			_error=ITLA_CSERROR
			return(byte0,byte1,byte2,byte3)

	def Receive_simple_response(self,sercon):
		global _error,CoBrite
		reftime=time.clock()
		while sercon.inWaiting()<4:
			if time.clock()>reftime+0.25:
				_error=ITLA_NRERROR
				return(0xFF,0xFF,0xFF,0xFF)
			time.sleep(0.0001)
		byte0=ord(sercon.read(1))
		byte1=ord(sercon.read(1))
		byte2=ord(sercon.read(1))
		byte3=ord(sercon.read(1))

	def ITLAConnect(self,port,baudrate=9600):
		global CoBrite
		reftime=time.clock()
		connected=False
		try:
			conn = serial.Serial(port,baudrate , timeout=1)
		except serial.SerialException:
			return(ITLA_ERROR_SERPORT)
		baudrate2=4800
		while baudrate2<115200:
			self.ITLA(conn,REG_Nop,0,0)
			if self.ITLALastError()<>ITLA_NOERROR:
				#go to next baudrate
				if baudrate2==4800:baudrate2=9600
				elif baudrate2==9600: baudrate2=19200
				elif baudrate2==19200: baudrate2=38400
				elif baudrate2==38400:baudrate2=57600
				elif baudrate2==57600:baudrate2=115200
				conn.close()
				
				conn = serial.Serial(port,baudrate2 , timeout=1)
			else:
				return(conn)
		conn.close()
		print('Dammit, couldnt find laser')
		conn = serial.Serial(port,baudrate2 , timeout=1)
		print(ITLA_ERROR_SERBAUD)
		return(ITLA_ERROR_SERBAUD)

	def ITLA(self,sercon,register,data,rw):
		global latestregister
		lock=threading.Lock()
		lock.acquire()
		global queue
		global maxrowticket
		rowticket=maxrowticket+1
		maxrowticket=maxrowticket+1
		queue.append(rowticket)
		lock.release()
		while queue[0]<>rowticket:
			rowticket=rowticket
		if rw==0:
			byte2=int(data/256)
			byte3=int(data-byte2*256)
			latestregister=register
			self.Send_command(sercon,int(self.checksum(0,register,byte2,byte3))*16,register,byte2,byte3)
			test=self.Receive_response(sercon)
			b0=test[0]
			b1=test[1]
			b2=test[2]
			b3=test[3]
			if (b0&0x03)==0x02:
				test=AEA(sercon,b2*256+b3)
				lock.acquire()
				queue.pop(0)
				lock.release()
				return test
			lock.acquire()
			queue.pop(0)
			lock.release()
			return b2*256+b3
		else:
			byte2=int(data/256)
			byte3=int(data-byte2*256)
			self.Send_command(sercon,int(self.checksum(1,register,byte2,byte3))*16+1,register,byte2,byte3)
			test=self.Receive_response(sercon)
			lock.acquire()
			queue.pop(0)
			lock.release()
			return(test[2]*256+test[3])

	def ITLA_send_only(self,sercon,register,data,rw):
		global latestregister
		global queue
		global maxrowticket
		rowticket=maxrowticket+1
		maxrowticket=maxrowticket+1
		queue.append(rowticket)
		while queue[0]<>rowticket:
			time.sleep(.1)
		SerialLockSet()
		if rw==0:
			latestregister=register
			self.Send_command(sercon,int(self.checksum(0,register,0,0))*16,register,0,0)
			Receive_simple_response(sercon)
			SerialLockUnSet()
		else:
			byte2=int(data/256)
			byte3=int(data-byte2*256)
			self.Send_command(sercon,int(self.checksum(1,register,byte2,byte3))*16+1,register,byte2,byte3)
			Receive_simple_response(sercon)
			SerialLockUnSet()
         
	def AEA(self,sercon,bytes):
		outp=''
		while bytes>0:
			self.Send_command(sercon,int(self.checksum(0,REG_AeaEar,0,0))*16,REG_AeaEar,0,0)
			test=self.Receive_response(sercon)
			outp=outp+chr(test[2])
			outp=outp+chr(test[3])
			bytes=bytes-2
		return outp

	def ITLAFWUpgradeStart(self,sercon,raydata,salvage=0):
		global tempport,raybin
		#set the baudrate to maximum and reconfigure the serial connection
		if salvage==0:
			ref=stripString(ITLA(sercon,REG_Serial,0,0))
			if len(ref)<5:
				print 'problems with communication before start FW upgrade'
				return(sercon,'problems with communication before start FW upgrade')
			ITLA(sercon,REG_Resena,0,1)
		ITLA(sercon,REG_Iocap,64,1) #bits 4-7 are 0x04 for 115200 baudrate
		#validate communication with the laser
		tempport=sercon.portstr
		sercon.close()
		sercon = serial.Serial(tempport, 115200, timeout=1)
		if stripString(ITLA(sercon,REG_Serial,0,0))<>ref:
			return(sercon,'After change baudrate: serial discrepancy found. Aborting. '+str(stripString(ITLA(sercon,REG_Serial,0,0)))+' '+str( params.serial))
		#load the ray file
		raybin=raydata
		if (len(raybin)&0x01):raybin.append('\x00')
		ITLA(sercon,REG_Dlconfig,2,1)  #first do abort to make sure everything is ok
		#print ITLALastError()
		if ITLALastError()<>ITLA_NOERROR:
			return( sercon,'After dlconfig abort: error found. Aborting. ' + str(ITLALastError()))
		#initiate the transfer; INIT_WRITE=0x0001; TYPE=0x1000; RUNV=0x0000
		#temp=ITLA(sercon,REG_Dlconfig,0x0001 ^ 0x1000 ^ 0x0000,1)
		#check temp for the correct feedback
		ITLA(sercon,REG_Dlconfig,3*16*256+1,1) # initwrite=1; type =3 in bits 12:15
		#print ITLALastError()
		if ITLALastError()<>ITLA_NOERROR:
			return(sercon,'After dlconfig init_write: error found. Aborting. '+str(ITLALastError() ))
		return(sercon,'')

	def ITLAFWUpgradeWrite(self,sercon,count):
		global tempport,raybin
		#start writing bits
		teller=0
		while teller<count:
			ITLA_send_only(sercon,REG_Ear,struct.unpack('>H',raybin[teller:teller+2])[0],1)
			teller=teller+2
		raybin=raybin[count:]
		#write done. clean up
		return('')

	def ITLAFWUpgradeComplete(self,sercon):
		global tempport,raybin
		time.sleep(0.5)
		sercon.flushInput()
		sercon.flushOutput()
		ITLA(sercon,REG_Dlconfig,4,1) # done (bit 2)
		if ITLALastError()<>ITLA_NOERROR:
			return(sercon,'After dlconfig done: error found. Aborting. '+str(ITLALastError()))
		#init check
		ITLA(sercon,REG_Dlconfig,16,1) #init check bit 4
		if ITLALastError()==ITLA_CPERROR:
			while (ITLA(sercon,REG_Nop,0,0)&0xff00)>0:
				time.sleep(0.5)
		elif ITLALastError()<>ITLA_NOERROR:
			return(sercon,'After dlconfig done: error found. Aborting. '+str(ITLALastError() ))
		#check for valid=1
		temp=ITLA(sercon,REG_Dlstatus,0,0)
		if (temp&0x01==0x00):
			return(sercon,'Dlstatus not good. Aborting. ')
		#write concluding dlconfig
		ITLA(sercon,REG_Dlconfig,3*256+32, 1) #init run (bit 5) + runv (bit 8:11) =3
		if ITLALastError()<>ITLA_NOERROR:
			return(sercon, 'After dlconfig init run and runv: error found. Aborting. '+str(ITLALastError()))
		time.sleep(1)
		#set the baudrate to 9600 and reconfigure the serial connection
		ITLA(sercon,REG_Iocap,0,1) #bits 4-7 are 0x0 for 9600 baudrate
		sercon.close()
		#validate communication with the sercon
		sercon = serial.Serial(tempport, 9600, timeout=1)
		ref=stripString(ITLA(sercon,REG_Serial,0,0))
		if len(ref)<5:
			return( sercon,'After change back to 9600 baudrate: serial discrepancy found. Aborting. '+str(stripString(ITLA(sercon,REG_Serial,0,0)))+' '+str( params.serial))
		return(sercon,'')

	def ITLASplitDual(self,input,rank):
		
		teller=rank*2
		return(ord(input[teller])*256+ord(input[teller+1]))

	##############################################################################################################
	# 	This is the beginning of function written by Matt Berrington. Functions prior to this are proivided by PurePhotonics
	# 	Functions you should only need if you want to manually address known registers for troubleshooting etc
	##############################################################################################################


	def ProbeLaser(self):
		#Apparently when you write zeroes to the laser, it should have a specific repsonse. It's a decent test to see if the laser is behaving.
		self.Send_command(self.sercon,0x00,0x00,0x00,0x00)
		response = self.Receive_response(self.sercon)
		if response != (84, 0, 0, 16):
			print('Laser is not behaving! Turning the laser off...')
			self.EnableLaser(self.sercon,False)
			sys.exit()

	def SendReceive(self,readwrite,register,byte2,byte3):
		#This self.SendReceive command should be all you need if you want to manually address a known register
		#Bytes 2 and 3 contain the number value
		self.Send_command(self.sercon,*self.CommandWithChecksum(readwrite,register,byte2,byte3))
		byte0, byte1, byte2, byte3 = self.Receive_response(self.sercon)
		response = (byte2 << 8) + byte3
		return response

	def PrintHex(self,list):
		HexList = []
		for byte in list:
			HexList.append((format(byte,'#02x')))
		print(HexList)

	def CommandWithChecksum(self,byte0,byte1,byte2,byte3):
		newbyte0 = (self.checksum(byte0,byte1,byte2,byte3)<<4) + byte0
		return newbyte0, byte1, byte2, byte3

	##############################################################################################################
	# 	Basic functions you'll probably always need
	##############################################################################################################

	def SetWavelength(self,wavelength):
		#Specify wavelength in nm. Note the wavelength will the rounded to the nearest 0.1GHz
		freq = round((2.99792*10**8/(wavelength*10**-9))*10**-12,4)
		#Set THz register
		freqTHz = int(freq)
		THzbyte3 = freqTHz&0xff
		THzbyte2 = (freqTHz&0xff00)>>8
		self.SendReceive(WRITE,REG_Fcf1,THzbyte2,THzbyte3)

		#Set GHz register
		freqGHz = int((freq-freqTHz)*10000)
		GHzbyte3 = freqGHz&0xff
		GHzbyte2 = (freqGHz&0xff00)>>8
		self.SendReceive(WRITE,REG_Fcf2,GHzbyte2,GHzbyte3)
		
		#Check what frequency is now set to
		THz = self.SendReceive(READ,REG_Fcf1,0,0)
		GHz = self.SendReceive(READ,REG_Fcf2,0,0)
		if THz == freqTHz and GHz == freqGHz:
			print('Frequency set to ' + str(freqTHz) + '.' + str(freqGHz) + ' THz')
			logging.info("Laser frequency set to " + str(freqTHz) + "." + str(freqGHz) + " THz")
		else:
			print('Failed to change laser frequency. Laser needs to be turned off')
			logging.error("Failed to change laser frequency. Laser needs to be turned off")

	def SetFrequency(self,freq):
		#Specify wavelength in THz
		#Set THz register
		freqTHz = int(freq)
		THzbyte3 = freqTHz&0xff
		THzbyte2 = (freqTHz&0xff00)>>8
		self.SendReceive(WRITE,REG_Fcf1,THzbyte2,THzbyte3)

		#Set GHz register
		freqGHz = int(round((freq-freqTHz)*10000.0))
		GHzbyte3 = freqGHz&0xff
		GHzbyte2 = (freqGHz&0xff00)>>8
		self.SendReceive(WRITE,REG_Fcf2,GHzbyte2,GHzbyte3)
		
		#Check what frequency is now set to
		THz = self.SendReceive(READ,REG_Fcf1,0,0)
		GHz = self.SendReceive(READ,REG_Fcf2,0,0)
		if THz == freqTHz and GHz == freqGHz:
			print('Frequency set to ' + str(freqTHz) + '.' + str(freqGHz) + ' THz')
			logging.info("Laser frequency set to " + str(freqTHz) + "." + str(freqGHz) + " THz")
		else:
			print('Failed to change laser frequency. Laser needs to be turned off')
			logging.error("Failed to change laser frequency. Laser needs to be turned off")

	def SetPower(self,power):
		#Specify power in dBm
		byte3 = power&0xff
		byte2 = (power&0xff00)>>8
		self.SendReceive(WRITE,REG_Power,byte2,byte3)
		logging.info("Laser power set to " + str(power) + " dBm")

	def EnableLaser(self,state):
		if state == True:
			logging.info("Turning on laser...")
			self.SendReceive(WRITE,REG_Resena,0x00,0x08)
			print('Please wait, laser is turning on...')
			self.WaitForLaser()
			logging.info("Laser is on")
			print('Laser is on')
		else:
			self.SendReceive(WRITE,REG_Resena,0x00,0x00)
			logging.info("Laser disabled")
			print('Laser is off')

	def WaitForLaser(self):
		#A loop that will halt code execution until the pending flag on the laser gives the thumbs up
		#This function is called when you enable the laser. You might want to use it when using the fine-tune frequency feature
		pending = 1
		while pending:
			self.Send_command(self.sercon,0x00,0x00,0x00,0x00)
			pending = self.Receive_response(self.sercon)[2]
			time.sleep(0.5)

	def EnableWhisperMode(self,state):
		if state == True:
			self.SendReceive(WRITE,REG_Mode,0x00,0x02)
			print("Whisper mode enabled")
			logging.info("Whisper mode enabled")
			time.sleep(0.5)
		else:
			self.SendReceive(WRITE,REG_Mode,0x00,0x00)
			print("Whisper mode disabled")
			logging.info("Whisper mode disabled")
			time.sleep(0.5)

	##############################################################################################################
	# 	Functions for the Clean Sweep feature
	##############################################################################################################

	def SetSweepRange(self,range):
		#Specify range in GHz
		byte3 = range&0xff
		byte2 = (range&0xff00)>>8
		self.SendReceive(WRITE,REG_Csweepamp,byte2,byte3)
		logging.info("Sweep range set to " + str(range) + " GHz")

	def SetSweepRate(self,rate):
		#Specify range in MHz/s
		byte3 = rate&0xff
		byte2 = (rate&0xff00)>>8
		self.SendReceive(WRITE,REG_Cscanf1,byte2,byte3)
		logging.info("Sweep rate set to " + str(rate) + " MHz/s")

	def EnableSweep(self,state):
		if state == True:
			self.SendReceive(WRITE,REG_Csweepsena,0x00,0x01)
			logging.info("Laser sweep enabled")
			print("Sweep enabled")
		else:
			self.SendReceive(WRITE,REG_Csweepsena,0x00,0x00)
			logging.info("Laser sweep disabled")
			print("Sweep disabled")

	def ReadOffsetFreq(self):
		#Reads the current frequency offset of the sweep in GHz
		#Can be buggy if you don't have a small delay between starting sweep and using this function
		data = self.SendReceive(READ,REG_Csweepoffset,0x00,0x00)
		if data > 65535/2:
			data = (data - 65535)*0.1
                else:
                        data *=0.1
		return data
	##############################################################################################################
	# 	Functions for the Clean Sweep feature
	#	Note I haven't used these functions thoroughly so there might be bugs
	##############################################################################################################

	def SetNextFrequency(self,freq):
		#Set THz register
		freqTHz = int(freq)
		THzbyte3 = freqTHz&0xff
		THzbyte2 = (freqTHz&0xff00)>>8
		dataTHz = self.SendReceive(WRITE,REG_CjumpTHz,THzbyte2,THzbyte3)
		
		#Set GHz register
		freqGHz = int(round((freq-freqTHz)*10000.0))
		GHzbyte3 = freqGHz&0xff
		GHzbyte2 = (freqGHz&0xff00)>>8
		dataGHz = self.SendReceive(WRITE,REG_CjumpGHz,GHzbyte2,GHzbyte3)
		print('Next jump frequency set to ' + str(dataTHz) + '.' + str(dataGHz) + ' THz')
		logging.info("Next jump frequency set to " + str(dataTHz) + "." + str(dataGHz) + " THz")

	def SetNextSled(self,sled):
		sled = int(sled*100)
		byte3 = sled&0xff
		byte2 = (sled&0xff00)>>8
		datasled = self.SendReceive(WRITE,REG_CjumpSled,byte2,byte3)
		logging.info("Next jump sled set to " + str(datasled/100.0) + " C")

	def SetNextCurrent(self,current):
		current = int(current*10)
		byte3 = current&0xff
		byte2 = (current&0xff00)>>8
		datacurrent = self.SendReceive(WRITE,REG_CjumpCurrent,byte2,byte3)
		logging.info("Next jump current set to " + str(datacurrent/10.0) + " mA")

	def ExecuteJump(self):
		logging.info("Executing jump")
		print("Executing jump")
		#You need to send the command four times:
		#First transfers frequency, temperature and current to memory
		#Second calculates filter 1
		#Third calculates fitler 2
		#Fourth executes the jump
		self.SendReceive(WRITE,REG_Cjumpon,0x00,0x01)
		self.SendReceive(WRITE,REG_Cjumpon,0x00,0x01)
		self.SendReceive(WRITE,REG_Cjumpon,0x00,0x01)
		self.SendReceive(WRITE,REG_Cjumpon,0x00,0x01)

	def FineTuneFrequency(self,ftf):
		byte3 = ftf&0xff
		byte2 = (ftf&0xff00)>>8
		self.SendReceive(WRITE,REG_Ftf,byte2,byte3)
		logging.info("Fine tune frequency set to " + str(ftf))

	##############################################################################################################
	# 	Other functions
	##############################################################################################################

	def ReadTemp(self):
		#I think this reads laser temperature
		data = self.SendReceive(READ,0x43,0x00,0x00)
		data = data*0.01
		logging.info("Laser temperature is " + str(data))
		return data

	def ReadDeviceTemp(self):
		#This reads the 'device temperature' instead of the 'laser temperature'. I'm unsure what the difference is
		data = self.SendReceive(READ,0x58,0x00,0x00)
		data = data
		logging.info("Device temperature is " + str(data))
		return data

	def ReadDeviceCurrent(self):
		data = self.SendReceive(READ,0x57,0x00,0x00)
		data = data
		logging.info("Device current is " + str(data))
		return data