import ctypes
import numpy
import traceback
import time
import pdb

#channel_map = {'ch1':0, 'ch2':1, 'ch3':2, 'ch4':3, 'ch5':4, 'ch6':5, 'ch7':6, 'ch8':7}#, 'microwave':3, 'trigger':4, 'SequenceTrigger':55, 'awgTrigger':0}
channel_map = {'ch{}'.format(n+1):n for n in range(20)}
CLOCK = 500.0
DT = 2.5

s = 1
ms = 10**-3
us = 10**-6
ns = 10**-9

dll = ctypes.cdll.LoadLibrary('spinapi.dll')

PULSE_PROGRAM  = 0
CONTINUE       = 0
STOP           = 1
LOOP           = 2
END_LOOP       = 3
LONG_DELAY     = 7
BRANCH         = 6
WAIT           = 8;
#ON             = 6<<21 # this doesn't work even though it is according to documentation
ON             = 0xE00000

def chk(err):
    """a simple error checking routine"""
    if err < 0:
        dll.pb_get_error.restype = ctypes.c_char_p
        err_str = dll.pb_get_error()
        #raise RuntimeError('PulseBlaster error: %s' % err_str)
        print err_str
        #pi3d.get_logger().error('PulseBlaster error: ' + err_str + ''.join(traceback.format_stack()))

def High(channels):
    """Set specified channels to high, all others to low."""
    #pi3d.get_logger().debug(str(channels))
    dll.pb_close()
    chk(dll.pb_init())
    chk(dll.pb_set_clock(ctypes.c_double(CLOCK)))
    chk(dll.pb_start_programming(PULSE_PROGRAM))
    chk(dll.pb_inst_pbonly(ON|flags(channels), STOP, None, ctypes.c_double(100)))
    chk(dll.pb_stop_programming())
    chk(dll.pb_start())
    chk(dll.pb_close())

def Sequence(sequence, loop=True, bStart=True):
    """Run sequence of instructions
    James 18-09-05 added check for whether a [step] in sequence is the start for a loop
    If so, records this instruction as LOOP_INST so END_LOOP can reference it
    """
    #pi3d.get_logger().debug(str(sequence))
    #we pb_close() without chk(): this might create an error if board was already closed, but resets it if it was still open
    dll.pb_close()
    chk(dll.pb_init())
    chk(dll.pb_set_clock(ctypes.c_double(CLOCK)))
    chk(dll.pb_start_programming(PULSE_PROGRAM))
    start = write(*sequence[0]) 
    count = 1 #Keep track of instr number for looping
    for step in sequence[1:]:
        
        ################### NEW 18-09-05 #################
        ###### FOR INTERNAL LOOPING ######################
        if len(step) > 2: #Probably a more elegant way to do this
            if step[2] == LOOP: #If an internal loop is desired we need to keep track of the loop start
                LOOP_INST = count
            elif step[2] == END_LOOP and len(step) < 4: #If END_LOOP instruction data is not given
                #then END_LOOP returns back to most recent LOOP instruction
                if 'LOOP_INST' not in locals(): #the start of the loop as instruction data
                    raise RuntimeError, "Start of LOOP must be defined before the END_LOOP"
                else:
                    step = step + (LOOP_INST,)
        #########################################
        
        label = write(*step)
        if label > 2**12 - 2:
            print 'WARNING in PulseBlaster: command %i exceeds maximum number of commands.' % label
        count +=1
    channels, dt = sequence[-1]
#    N = int(numpy.round(dt/DT))
#    if N > 256:
#        raise RuntimeError, 'Length in STOP / BRANCH exceeds maximum value.'
    if loop == False:
        label = chk(dll.pb_inst_pbonly(ON|flags(channels), STOP, None, ctypes.c_double( 12.5 ) ))
    else:
        label = chk(dll.pb_inst_pbonly(ON|flags([]), BRANCH, start, ctypes.c_double( 12.5 ) ))
    if label > 2**12 - 2 :
        print 'WARNING in PulseBlaster: command %i exceeds maximum number of commands.' % label
    chk(dll.pb_stop_programming())
    if bStart:
        chk(dll.pb_start())
    chk(dll.pb_close())


def write(channels, dt, inst=CONTINUE, instData=None):
    #James 18-09-05 added instData=None, to allow for instruction data for commands (flags?)
    #such as LOOP and END_LOOP
    channel_bits = flags(channels)
    dt = dt*(10**9)
    N = int(numpy.round( dt / DT ))

    #pdb.set_trace()
    if N <= 2**12:
        label = chk(dll.pb_inst_pbonly( ON|channel_bits, inst, instData, ctypes.c_double( N*DT ) ))
    else:
        # successively try factorization, reducing N, and putting the subtracted amount into an additional short command if necessary
        B = N
        i = 4
        while True:
            M, K = factor(N)
            if M > 4:
                if K == 1:
                    label = chk(dll.pb_inst_pbonly( ON|channel_bits, inst, instData, ctypes.c_double( M*DT ) ))
                elif K < 1048577:
                    if inst != CONTINUE:
                        raise ValueError("Can't do a non-CONTINUTE instruction that is so long (>40us)")
                    label = chk(dll.pb_inst_pbonly( ON|channel_bits, LONG_DELAY, K, ctypes.c_double( M*DT ) ))
                else:
                    raise RuntimeError, 'Loop count in LONG_DELAY exceedes maximum value.'
                if i > 4:
                    chk(dll.pb_inst_pbonly( ON|channel_bits, inst, instData, ctypes.c_double( i*DT )  ))
                break
            i += 1
            N = B - i
    return label

def flags(channels):
    bits = 0
    for channel in channels:
        bits = bits | 1<<channel_map[channel]
        
    return bits


def factor(x):    
    i = 2**12
    while i > 4:
        if x % i == 0:
            return i, x/i
        i -= 1
    return 1, x

def ch2():
    Sequence([(['ch2','ch5'], 1*s)],loop=False)
##     Sequence([(['ch2'], 1*s)],loop=False)

def all_off():
    Sequence([([]), 1*us],loop=False)

def on_off():
    Sequence([(['ch5'], 3*s),
    (['ch6'], 3*s)
    ],loop=True)
    

def hole_burn(burn_time = 1*s,n=1):
    ''' Simple hole burn sequence.
        Waits 0.5s for code to catch up, burns hole for set time, changes DC bias
        on EOM, Triggers the Spec An to sweep, lets the Spec An continuously sweep after.
    '''

    array = [([], 0.5*s),(['ch1'], burn_time)] + [(['ch5'], 1000*ms), (['ch2','ch4','ch5'], 100*ms)] + [(['ch2','ch5'], 100*ms)]

    
    Sequence(array,loop=False)
    
    
## def trigger_SpecAn(n=1):
##     #Figure out how to make this loop 10 times
##     
##     array = []
##     for i in range (n):
##         array = [(['ch2','ch4','ch5'], 50*ms),([], 1*us)] + array
##     return array
        

  

def fiber_prop():

    array1 =  [(['ch1'], 50*ms),([], 50*ms)]
    for i in range (1,4):
        array1 =  [(['ch1'], 50*ms),([], 50*ms)] + array1
        
 
    array2 = [(['ch1'], 500*ms),([], 500*ms),(['ch1'], 500*ms),([], 500*ms)]
    
    array3 = [(['ch1'], 100*ms),([], 200*ms)]
    for i in range (1,4):
        array3 =  [(['ch1'], 100*ms),([], 200*ms)] + array3
        
        
    array4 = [(['ch1'], 300*ms),([], 50*ms)]
    
    for i in range (1,4):
        array4 =  [(['ch1'], 300*ms),([], 50*ms)] + array4
    
   # print array4
    
    arrayfinal =  array1 + array1 + array1 + array2 + array3 + array2 + array4 + array3 + array1 + array4
    Sequence(arrayfinal,                #Sweep
    loop=True)

def mems_switch_toggle_latch(t,n=1,other_ch='',init_state = 1):
    ''' 
    NOTE: THIS IS FOR THE LATCHING MEMS SWITCHES ONLY
    Will toggle the state of the mems switches connected to Channel 6.
    n, allows for multiple repetitions.
    other_ch sets the channels during the 'off' state of the mems switches
    init_state allows us to record what the end state is (1 or 2)
    '''
    switch_ch = 'ch7'#'ch6'
    if t < 1*ms:
        raise('error: t must be > 1 ms')
    
    t = t - 20*us#This is to offset the 20us gap at the start of the array.
    
    if other_ch == '':
        array = [([switch_ch],20*us),([],t)] #The gap time must be larger than 10 us
        while n > 1:
            array = [([switch_ch],20*us),([],t)] + array
            n = n-1
    else:
        array = [([switch_ch],20*us),([other_ch],t)]
        while n > 1:
            array = [([switch_ch],20*us),([other_ch],t)] + array
            n = n-1
            
    #Turn init_state into binary 0 is state 1, 1 is state 2
    init_state -= 1        
    is_even_odd = n%2
    final_state = (init_state + is_even_odd)%2 + 1
    str = 'Final output state will be {0}'.format(final_state)
    print 'mems switch will toggle {} time(s), with {} s inbetween pulses.'
    print str
            
    Sequence(array, loop = False)
    return final_state
    
def toggle_latch_onoff(t):
    switch_ch = 'ch7'

    if t < 1*ms:
        raise('error: t must be > 1 ms')
    
    print('Switching MEMs for ' + str(t) + ' seconds')
    t = t - 1*ms#This is to offset the 20us gap at the start of the array.
    array = [(['ch7'],1*ms) , ([],t) , (['ch7'],1*ms) , (['ch5'],1*ms)]
    Sequence(array, loop = False)
    
    
def mems_switch_toggle(t,n=1, t2 = 1*ms, other_ch = '', init_state = 0):
    if t < 1*ms:
        raise('error: t must be > 1 ms')
    
    print "Toggling MEMS switch high for {} s".format(t)
    if n > 1:
        print "Toggling MEMS switch low for {} s, repeating {} times".format(t2, n)
    
    array = [(['ch6'],t),([],t2)]
    while n > 1:    
        array = array + [(['ch6'],t),([],t2)]
        n = n-1
    Sequence(array,loop = False)
    
    
def ProbBurn(shots = 1000):
    ''' Spin polarises the crystal for 10s via CH6, then loops through waiting for a 
    triggering keeping CH1 open (RF switch for AWG), and pulses CH3 to trig picoscope.
    Always keeps CH5 open (EOM bias)'''
    shots = shots + 1
    
    arr = [(['ch5','ch6'], 10*s), (['ch5'], 20*ms)] #10s to spin pol. crystal, 20ms to let the mems switch switch.  
    Sequence(arr,loop=False)
    time.sleep(10.1)
        
    ProbBurnLoop(shots)
    
    
def ProbBurnLoop(shots = 1000):
    
    #I want this is wait a certain amount of time before looping back to the next AWG sequence
    arr = [(['ch5'], 0.5*us),            #Cant LOOP on first command 
    (['ch1','ch5'], 0.5*us, LOOP, shots),#LOOP through recording the PulseBurns    
    (['ch1','ch3','ch5'], 1*us, WAIT),          #Trig PS to record
    (['ch1','ch5'], 1*us, END_LOOP),    #END of LOOP
    (['ch5'], 1*ms)                      #After looping close RF switches
    ]
    Sequence(arr,loop=False,bStart=False)
    

def LOOP_test():
    arr = [(['ch7'], 0.01*ms),
    ([], 10*us),
    (['ch7'], 5*us, LOOP, 10),
    ([],5*us, END_LOOP),
    ([], 10*us)
    ]
    Sequence(arr,loop=False)

if __name__ == '__main__':
    
    #Light()
##     mems_switch_toggle(10*s,n=1, t2 = 1*ms, other_ch = '', init_state = 0)
##     time.sleep(10)
##     Sequence([(['ch2','ch5','ch3'], 2.5*ms),(['ch5'],2.5*ms)], loop=True)
    Sequence([(['ch3'], 1*ms) , ([], 1*ms)], loop=False)
    
##     test = True
##     if test:
##         Sequence([(['ch2','ch5'], 1*s)], loop=False)
##     else:
##         Sequence([(['ch2','ch3'], 1*us) , ([], 5*ms)], loop=True)
        
##     
##     toggle_latch_onoff(t=1)
##     Sequence([(['ch2','ch5'], 2.5*ms)], loop=False)
##     ProbBurnLoop(shots = 2000)

##     import James_AFC_V1 as James
##     James.AWG_trig_out()
##     ProbBurn()

    
##     Sequence([([], 1*us), ([], 10*us, WAIT), (['ch7'], 10*us),([], 10*us), ([], 100*us)], loop=True, bStart=False)

##     storage_arr = [(['ch3','ch5'], 1*us),(['ch1','ch5'], 500*us),(['ch5'], 1*ms)]
##     storage_arr = [(['ch3','ch5'], 1*ms),(['ch7','ch5'], 1*ms),(['ch5'], 9*ms)]
##     Sequence(storage_arr,loop = False)
    

##     Sequence([(['ch6'], 20*us),([],980*us)], loop=False)
##     mems_switch_toggle(1)
##     Sequence([(['ch3'], 1*ms), ([], 1*ms)],loop=True)
##     on_off()
##     trigger_SpecAn()
    #Night()
    #print factor(1023)
    
    
   
