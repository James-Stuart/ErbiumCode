"""used to be just to upload chirps etc. Now does more. Needs refactoring!
Soon James, soon!
"""

import sys
pth = 'C:/Users/Milos/pythonpackages'
if pth not in sys.path:
    sys.path.append(pth)
from pyADS7 import pyADS7
from collections import OrderedDict
#import pdb
import numpy as np



wvfmD = None
ads7 = None

#def setup(centerFreqL=[ -100e6, 300e6, 500e6], firstWidth=0, chirpWidth=500e3, sweepTime= 1e-3, NCO_freq=0, bChirpUpDown=False):
def setup(centerFreqL=[ -100e6, 300e6, 500e6], widthL=[0, 500e3, 500e3], sweepTimeL= [1e-3, 1e-3, 1e-3], NCO_freq=0, bChirpUpDown=False):

	"""Make sure you setup the ADS7 to be in the usual complex mode"""
	global ads7
	if ads7 is None:
		initForJames()
	ads7.outputOff()
	
	Nwvs = len(centerFreqL)
	#Make sure the arguments are iterable. Also, assume any missing values are same as the last one,
	if not np.iterable(widthL):
		widthL = [widthL]
	if len(widthL) < Nwvs:
		widthL = list(widthL) + (Nwvs-len(widthL))*widthL[-1:]
	if not np.iterable(sweepTimeL):
		sweepTimeL = [sweepTimeL]
	if len(sweepTimeL) < Nwvs:
		sweepTimeL = list(sweepTimeL) + (Nwvs-len(sweepTimeL))*sweepTimeL[-1:]
	
	nextAddrOffs = 0;
	global wvfmD
	wvfmD = OrderedDict()
	
	#for k, cf in enumerate(centerFreqL):
	for cf, chirpW, sweepTime in zip(centerFreqL, widthL, sweepTimeL):
		centerFreq = cf - NCO_freq
		#chirpW = chirpWidth if k!=0 else firstWidth
		if bChirpUpDown:
			I, Q = pyADS7.make2WayQuadrChirp(centerFreq - chirpW/2, centerFreq + chirpW/2, sweepTime, FDAC = 2500000000)
		else:
			I, Q = pyADS7.makeQuadrChirp(centerFreq - chirpW/2, centerFreq + chirpW/2, sweepTime, FDAC = 2500000000)
		print("Sending {}".format(centerFreq))
		startAddr, playLength = ads7.sendChunked(I,Q, addrOffs=nextAddrOffs)
		#pdb.set_trace()
		wvfmD[cf] = [startAddr, playLength]
		nextAddrOffs += playLength
	setWvfm(0)
	return wvfmD, nextAddrOffs
	
def addWvfm(I,Q, name=None):
	global wvfmD
	newAddrOffs= sum(list(wvfmD.values())[-1])
	startAddr, playLength = ads7.sendChunked(I,Q, addrOffs=newAddrOffs)
	if name is None:
		name = 'added ' + str(len(wvfmD)-1)
	wvfmD[name] = [startAddr,playLength]
	nextAddrOffs = startAddr + playLength
	return wvfmD, nextAddrOffs
	
	
	
	
def setupCombs(Nteeth=5, spacing=1e6, fracOffset=0, centerFreqL=[500e6, 100e6], widthL=[0, 500e3], sweepTimeL= [1e-3, 1e-3], bChirpUpDown=False):
	#pdb.set_trace()
	baseCombFreqs = spacing*np.arange(Nteeth,dtype='f8') - (Nteeth-1 + fracOffset)*spacing/2
	
	newFreqL = list(np.hstack([baseCombFreqs+freq for freq in centerFreqL]))
	newWidthL = list(np.hstack([Nteeth*[width] for width in widthL]))
	newSweepTimeL = list(np.hstack([Nteeth*[swpTime] for swpTime in sweepTimeL]));
	return setup(newFreqL, newWidthL, newSweepTimeL, bChirpUpDown=bChirpUpDown)
	#return newFreqL, newWidthL, newSweepTimeL
	
def setupCombs2(Nteeth=5, spacing=1e6, fracOffset=0, centerFreqL=[500e6, 100e6], widthL=[0, 500e3], sweepTimeL= [1e-3, 1e-3],
		centerFreqAntiL=[], widthAntiL=[], sweepTimeAntiL=[], bChirpUpDown=False):
	"""setupCombs and also anti-combs
	
	The anti-combs have 1 more tooth than the combs, are offset by half a tooth spacing, and have chirp widths of (spacing-width)
	Morgan has not tested this!
	"""
	if not len(centerFreqL) == len(widthL) == len(sweepTimeL):
		raise ValueError("Not all the things are the same length!")
	if not len(centerFreqAntiL) == len(widthAntiL) == len(sweepTimeAntiL):
		raise ValueError("Not all the anti-things are the same length!")
	#pdb.set_trace()
	
	baseCombFreqs = spacing*np.arange(Nteeth,dtype='f8') - (Nteeth-1 + fracOffset)*spacing/2
	baseAntiCombFreqs = spacing*np.arange(Nteeth+1,dtype='f8') - (Nteeth + fracOffset)*spacing/2
	
	newFreqL = list(np.hstack([baseCombFreqs+freq for freq in centerFreqL]))
	newWidthL = list(np.hstack([Nteeth*[width] for width in widthL]))
	newSweepTimeL = list(np.hstack([Nteeth*[swpTime] for swpTime in sweepTimeL]));
	
	if len(centerFreqAntiL)>0:
		newFreqAntiL = list(np.hstack([baseAntiCombFreqs+freq for freq in centerFreqAntiL]))
		newWidthAntiL = list(np.hstack([(Nteeth+1)*[spacing-width] for width in widthAntiL])) #Width is 1-spacing
		newSweepTimeAntiL = list(np.hstack([(Nteeth+1)*[swpTime] for swpTime in sweepTimeAntiL]));
	else:
		newFreqAntiL, newWidthAntiL, newSweepTimeAntiL = [],[],[]
	
	return setup(newFreqL+newFreqAntiL, newWidthL+newWidthAntiL, 
			newSweepTimeL+newSweepTimeAntiL, bChirpUpDown=bChirpUpDown)
	#return newFreqL, newWidthL, newSweepTimeL
	
	
def setPulse(freq = 1e8, bw = 1e6, shp = 'Gaussian', npt = 16384, nextAddr = 0):
	"""Runs the makePulse funciton in pyADS7 and uploads to the AD9164 AWG
	OLD CODE"""
	
	#======= NOT YET FINISHED NEED TO ADD UPLOADING AND INTEGRATE WITH OTHER UPLOAD FUNCTIONS =======
	
	global ads7
	if ads7 is None: #Check the ADS7 AWG
		initForJames()
	ads7.outputOff()
	
        if nextAddr in locals():
            nextAddrOffs = nextAddr
        else:
            nextAddrOffs = 0
        
	global wvfmD
	#wvfmD = OrderedDict()
	
	I, Q = pyADS7.makePulse(freq,bw, shape = shp, Npts = npt)
	
	print("Sending {}".format(freq))
	
	#Change this part
	startAddr, playLength = ads7.sendChunked(I,Q, addrOffs=nextAddrOffs)
	wvfmD['pulse'] = [startAddr, playLength]
	nextAddrOffs += playLength
	setWvfm(0)
	return wvfmD, nextAddrOffs
	

	
def setupCombPulse(freq=660.99e6,bw=3e6,Nteeth=5,spacing=1e6,centerFreqL=[500e6, 100e6],widthL=[0, 500e3],sweepTimeL= [1e-3, 1e-3]):

	""" """
            
	wvfmD, nextAddrOffs = setupCombs(Nteeth=Nteeth, spacing=spacing, fracOffset=0, centerFreqL=centerFreqL, widthL=widthL, sweepTimeL=sweepTimeL)
	
	I,Q = pyADS7.makeDelayedPulse(freq,bw,shape = 'Gaussian',time = 50e-6)
	addWvfm(I,Q, name="Pulse")
	
	
	
def setupCombPulse2(freq=660.99e6,bw=3e6,Nteeth=5,spacing=1e6,centerFreqL=[500e6, 100e6],widthL=[0, 500e3],sweepTimeL= [1e-3, 1e-3], centerFreqAntiL=[], widthAntiL=[], sweepTimeAntiL=[]):
	
	wvfmD, nextAddrOffs = setupCombs2(Nteeth=Nteeth, spacing=spacing, fracOffset=0, centerFreqL=centerFreqL, widthL=widthL, sweepTimeL=sweepTimeL, centerFreqAntiL =centerFreqAntiL, widthAntiL= widthAntiL, sweepTimeAntiL = sweepTimeAntiL)
	
	I,Q = pyADS7.makeDelayedPulse(freq,bw,shape = 'Gaussian',time = 50e-6)
	addWvfm(I,Q, name="Pulse")	

def setupProbeBurn(freq = 660.99e6, burnTime=5e-4, tPulseTotal=1e-4, tDelay=50e-6, bandwidth=5e6):
	global ads7
	if ads7 is None:
		initForJames()
	#ads7.outputOff()
	
	nextAddrOffs = 0;
	global wvfmD
	wvfmD = OrderedDict()
	
	#Make Just the single freq burn
	I3,Q3 = pyADS7.makeQuadrTone(freq, Nsamples= 163840)
	print("Sending Just the Burn single freq.")
	startAddr, playLength = ads7.sendChunked(I3,Q3, addrOffs=nextAddrOffs)
	#pdb.set_trace()
	wvfmD['Burn'] = [startAddr, playLength]
	nextAddrOffs += playLength		
	
	
	
	
	#Make & Upload Probe without Burn
	I,Q = pyADS7.makeProbeBurn(freq, burnTime, tPulseTotal+tDelay, tDelay, bandwidth, burn = False)
		
	print("Sending ReferencePulse")
	startAddr, playLength = ads7.sendChunked(I,Q, addrOffs=nextAddrOffs)
	#pdb.set_trace()
	wvfmD['ProbeReference'] = [startAddr, playLength]
	nextAddrOffs += playLength
	
	
	
	
	#Make and Upload Probe with Burn
	I2,Q2 = pyADS7.makeProbeBurn(freq, burnTime, tPulseTotal+tDelay, tDelay, bandwidth, burn = True)
	
	print("Sending BurnPulse")
	startAddr, playLength = ads7.sendChunked(I2,Q2, addrOffs=nextAddrOffs)
	#pdb.set_trace()
	wvfmD['ProbeBurn'] = [startAddr, playLength]
	nextAddrOffs += playLength
	
	
	setWvfm(0)
	return wvfmD, nextAddrOffs
	
	
def setupProbeBurnDelay(freq = 660.99e6, burnTime=5e-4, tPulseTotal=1e-4, tDelay=5e-6, bandwidth=5e6, blankTime = 1e-3, Nblank = 5):
	''' Sets up ProbeBurn and then uploads a number of blank waveforms to act as a
	delay between the burn and the probe read out'''
	wvfmD, nextAddrOffs = setupProbeBurn(freq, burnTime, tPulseTotal, tDelay, bandwidth)
	
	IBlank,QBlank = pyADS7.makeBlank(blankTime)
	for i in range(Nblank):
		print("Sending Blank {}".format(i+1))
		startAddr, playLength = ads7.sendChunked(IBlank,QBlank, addrOffs=nextAddrOffs)
		wvfmD['Blank ' +str(i)] = [startAddr, playLength]
		nextAddrOffs += playLength		
		
	setWvfm(0)
	return wvfmD, nextAddrOffs
		
		
		
	
def setWvfmKey(key):
	startAddr, playLength = wvfmD[key]
	ads7.playHere(startAddr, playLength)
	
	
def setWvfm(indexStart, indexStop=None):
	if indexStop is None:
		indexStop=indexStart;
		
	#ads7.outputOff()
	keyList=list(wvfmD.keys())[indexStart:indexStop+1]
	#keyStop = list(wvfmD.keys())[indexStop]
	playLength = sum([wvfmD[key][1] for key in keyList])
	print("Summed playLength is {}".format(playLength))
	startAddr= wvfmD[keyList[0]][0]
	ads7.playHere(startAddr, playLength)
	#ads7.outputOn();
	if 0:
		if freq not in wvfmD.keys():
			raise KeyError("haven't loaded a frequency of {}".format(freq))
		else:
			ads7.outputOff()
			ads7.playHere(*wvfmD[freq])
			ads7.outputOn();

def sync():
	ads7.syncAndGo()

def initForJames():
	global ads7
	ads7= pyADS7.Ads7();
	I, Q= pyADS7.make2WayQuadrChirp(100e6, 101e6, sweepTime=0.0001, FDAC = 2500000000)
	par1 = ads7.sendChunked(1*I,1*Q, addrOffs=int(1e9))
	ads7.syncAndGo()


if __name__=="__main__":
	#init()
	#, 200e6])
	setup(centerFreqL = [-50e6, 100e6])
	setWvfm(0)
	#sync()
	
