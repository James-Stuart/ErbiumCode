''' Picoscope 5000 series functions '''

from picoscope import ps5000a
import matplotlib.pyplot as plt
import numpy as np
import time


def open_pico(powerConnected = True):
        ps = ps5000a.PS5000a()
        
        if powerConnected:
            ps.changePowerSource("PICO_POWER_SUPPLY_CONNECTED")
            
        return ps
        
        
        
def setPicoTrace(ps, ch, Vrange, t_sample, t_record, trig = 0, res = None):
    ''' Set the picoscope up for data recording/streaming, and returns the settings
    ch = 'A','B' or ['A','B']
    Vrange, can be a list, if you want A and B to have different ranges
    t_sample,
    t_record,
    trig, defaults to 0 (no trigger) options: 'A', 'B', 'External'
    res = '8','12','14','15','16' (only 16 if only recording 1 channel)
    if res is not defined, the highest resolution will be used.
    '''
    
    #Not the best way to do this, but it'll work
    if len(ch) > 1:
        if type(Vrange) != list:
            ps.setChannel(channel='A', coupling = 'DC', VRange= Vrange)
            ps.setChannel(channel='B', coupling = 'DC', VRange= Vrange)
        else:
            #If you define two voltage ranges
            ps.setChannel(channel='A', coupling = 'DC', VRange= Vrange[0])
            ps.setChannel(channel='B', coupling = 'DC', VRange= Vrange[1])
    else:
        ps.setChannel(channel= ch, coupling = 'DC', VRange= Vrange)
    
    if res == None:
	if t_sample > 16e-9:
            if len(ch) == 1:
                    ps.setResolution('16')
                    res = 16
            else:
                    ps.setResolution('15')
                    res = 15
	elif t_sample <= 16e-9 and t_sample > 8e-9:
		ps.setResolution('14')
		res = 14
	elif t_sample <= 8e-9 and t_sample > 2e-9:
		ps.setResolution('12')
		res = 12
	else:
		ps.setResolution('8')
		res = 8
    else:
        ps.setResolution(res)
        
    ps.setSamplingInterval(t_sample, t_record)
    ps.setSimpleTrigger(trig,threshold_V = 1.0, direction = 'Rising')
    
    settings = {'Channel':ch, 'Range':Vrange, 'Tsample':t_sample, 'Tlength':t_record, 'Trigger':trig, 'Resolution':res}
    return settings
    

def getPicoTrace(ps, ch):
    '''Once picoscope is set up/setPicoTrace has been run, use this to get data.
    '''
    
    ps.runBlock()
    ps.waitReady()
    tStart = time.time()
    
    if len(ch)>1:
        A,l,b = ps.getDataRaw('A')
        B,l,b = ps.getDataRaw('B')
        output = getChannelSettings(ps,'A')
        settingsB = getChannelSettings(ps,'B')
        output['Brange'] = settingsB['Range'] #Probably a better way to do this
        output['A'] = A
        output['B'] = B
        
        
    else:
        data,length,boool = ps.getDataRaw(ch)
        output = getChannelSettings(ps,ch)
        output[ch] = data
        
    output['tStart'] = tStart
        
    return output
    

def getPicoTraceV(ps, ch):
    ''' Same as getPicoTrace, but returns data as voltages '''
    ps.runBlock()
    ps.waitReady()
    tStart = time.time()
    
    
    if len(ch)>1:
        A = ps.getDataV('A')
        B = ps.getDataV('B')
        output = getChannelSettings(ps,'A')
        settingsB = getChannelSettings(ps,'B')
        output['RangeB'] = settingsB['RangeB'] #Probably a better way to do this
        output['A'] = A
        output['B'] = B
        
    else:
        data = ps.getDataV(ch)
        output = getChannelSettings(ps,ch)
        output[ch] = data
        
    output['tStart'] = tStart
    
    return output


def getChannelSettings(ps, ch):
    ''' Get the voltage range, resolution and sample time for a given channel '''
    channel = {'A':0,'B':1}
    chNum = channel[ch]
    t_sample = ps.sampleInterval
    Vrange = ps.CHRange[chNum]
    resValue = ps.resolution
    
    for key,value in ps.ADC_RESOLUTIONS.items():
        if value == resValue:
            res = int(key)
    
    settings = {'Range'+ch:Vrange, 'Tsample':t_sample, 'Resolution':res}
    return settings
  
    

def setRapidBlock(ps, ch, Vrange, nCaptures, t_sample, t_record, trig = "External",
                  res = None):
    '''Rewritten the 'run_rapid_block' functions to match the getPicoTrace "style"
    ch = 'A','B','both'
    Vrange, can be a list, if you want A and B to have different ranges
    nCaptures, amount of data blocks returned
    t_sample,
    t_record,
    trig, defaults to 'External'. options: 'A', 'B', 'External'
    res = '8','12','14','15','16' (only 16 if only recording 1 channel)
    if res is not defined, the highest resolution will be used.
    '''
    settings = setPicoTrace(ps, ch, Vrange, t_sample, t_record, trig, res)
    #ps.setSimpleTrigger("External", threshold_V = 1.0, direction = 'Rising', timeout_ms = 15000)
    samples_per_segment = ps.memorySegments(nCaptures)
    ps.setNoOfCaptures(nCaptures)
    return settings


def getRapidBlock(ps):
    '''Rewritten the get_data_from_rapid_block function to match above "style" '''
    ps.runBlock()
    ps.waitReady()
    tStart = time.time()
    
    print("collecting data")
    
    A = ps.getDataRawBulk(channel='A')[0].squeeze()
    B = ps.getDataRawBulk(channel='B')[0].squeeze()
    data = getChannelSettings(ps,'A')
    dataSettingsB = getChannelSettings(ps,'B')
   
    data['A'] = A
    data['B'] = B
    data['RangeB'] = dataSettingsB['RangeB']
    data['tStart'] = tStart    

    return data    
    
    
    

# OLD RAPID BLOCK CODE BELOW
def run_rapid_block(ps, Vrange, n_captures, t_sample, record_length, chB = [False,False]):
	''' Records on CH A using Rapid block mode.
	Vrange = voltage range of channel A on pico
	n_captures = the number of data segments captured
	t_sample = time between each data point
	record_length = total time for the waveform recorded
        chB settings for recording channel B, first is enable = [True or False]
        second is Vrange, if False, records chA Vrange.
	
	Returns resolution in bits
	'''

	ps.setChannel(channel="A", coupling="DC", VRange=Vrange)
        #05-11-18 James added option for recording chB 
        if not chB[1]:
                chB[1] = Vrange
                ps.setChannel(channel='B', enabled="DC", VRange=chB[1])
          
      
       
	if t_sample > 16e-9:
                if not chB[0]:
                        ps.setResolution('16')
                        res = 16
                else:
                        ps.setResolution('15')
                        res = 15
	elif t_sample <= 16e-9 and t_sample > 8e-9:
		ps.setResolution('14')
		res = 14
	elif t_sample <= 8e-9 and t_sample > 2e-9:
		ps.setResolution('12')
		res = 12
	else:
		ps.setResolution('8')
		res = 8
		
	ps.setSamplingInterval(t_sample, record_length)
	#Give a long timeout (30s) incase of things running slow
	
	ps.setSimpleTrigger("External", threshold_V = 1.0, direction = 'Rising', timeout_ms = 15000) 
	#Pulseblaster should give 3.3V, so setting the threshold to be non-zero
	
	samples_per_segment = ps.memorySegments(n_captures)
	#samples_per_segment = int(record_length/t_sample)
	ps.setNoOfCaptures(n_captures)
	
	#data = np.zeros((n_captures, samples_per_segment), dtype=np.int16)
	
	ps.runBlock()
	#JAMES: If you're splitting up the data getting, why don't you put waitReady() in the get_data function? 
	#Otherwise you might as well get the data here.
	
	
	return t_sample, res


def get_data_from_rapid_block(ps):
	ps.waitReady()
        print("collecting data")
	return ps.getDataRawBulk(channel='A')[0].squeeze(),ps.getDataRawBulk(channel='B')[0].squeeze()

	#return data
		
def pico_plot(data, t_sample):
	''' Plots data from the picoscope '''
	#is data 1D or 2D?
	if data.ndim == 1:
		t = np.arange(data.size)*t_sample
		plt.plot(t , data)
		plt.show()
	else:
		#t = np.linspace(0,(len(data[:,1])-1)*t_sample,len(data[:,1])-1)
		t = np.arange(data.size)*t_sample
		#plt.imshow(data)
		#pdb.set_trace()
		#plt.plot(t,data[0,:])
		plt.show()
	


if __name__ == "__main__":
	import pulse_blaster as pb
        import scipy.io as sio
	try: 
                ps = open_pico()
		data,t_sample = run_rapid_block(ps, Vrange = 1, n_captures = 2, t_sample = 1e-8, record_length = 10e-6, chB=[False,False])
		pb.Sequence([([],1e-3),(['ch3'],1e-6),([],1e-3)],loop = False)
		data = get_data_from_rapid_block(ps)
# =============================================================================
# 		pico_plot(data,t_sample)
# =============================================================================
                filenameMat = "C:\Users\Milos\Desktop\James\\test2ch.mat"
                sio.savemat(filenameMat,{'DataPico':data})

	finally:
		ps.close()

