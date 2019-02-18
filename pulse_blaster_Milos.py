import ctypes
import numpy
import traceback

channel_map = {'ch1':0, 'ch2':1, 'ch3':2, 'ch4':3, 'ch5':4, 'ch6':5, 'ch7':6, 'ch8':7}
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


def Sequence(sequence, loop=True):
    """Run sequence of instructions"""
    #pi3d.get_logger().debug(str(sequence))
    #we pb_close() without chk(): this might create an error if board was already closed, but resets it if it was still open
    dll.pb_close()
    chk(dll.pb_init())
    chk(dll.pb_set_clock(ctypes.c_double(CLOCK)))
    chk(dll.pb_start_programming(PULSE_PROGRAM))
    start = write(*sequence[0])
    for step in sequence[1:]:
        label = write(*step)
        if label > 2**12 - 2:
            print 'WARNING in PulseBlaster: command %i exceeds maximum number of commands.' % label
    channels, dt = sequence[-1]
    
    if loop == False:
        label = chk(dll.pb_inst_pbonly(ON|flags(channels), STOP, None, ctypes.c_double( 12.5 ) ))
    else:
        label = chk(dll.pb_inst_pbonly(ON|flags([]), BRANCH, start, ctypes.c_double( 12.5 ) ))
    if label > 2**12 - 2 :
        print 'WARNING in PulseBlaster: command %i exceeds maximum number of commands.' % label
    chk(dll.pb_stop_programming())
    chk(dll.pb_start())
    chk(dll.pb_close())


def write(channels, dt):
    channel_bits = flags(channels)
    dt = dt*(10**9)
    N = int(numpy.round( dt / DT ))
    if N*DT < 8*10**9:  #apply this if pulse is shorter than 8 Seconds
        label = chk(dll.pb_inst_pbonly( ON|channel_bits, CONTINUE, None, ctypes.c_double( N*DT ) ))
    else:
        #need to factorise long number into units of 2 seconds and find remainded, which we add as a single pulse
        multiplier, remainder = factor(N)
        
        if multiplier < 1048577:
            label = chk(dll.pb_inst_pbonly( ON|channel_bits, LONG_DELAY, multiplier, ctypes.c_double( 2*(10**9)) ))
        else:
            raise RuntimeError, 'Loop count in LONG_DELAY exceedes maximum value.'
            
        chk(dll.pb_inst_pbonly( ON|channel_bits, CONTINUE, None, ctypes.c_double( remainder*DT )  ))

    return label

def flags(channels):
    bits = 0
    for channel in channels:
        bits = bits | 1<<channel_map[channel]
        
    return bits

def factor(x):
    
    # 2 seconds in units of clock cycles:
    divisor = (2*(10**9))/DT
    
    #calculate the remainder and mutiplier, Note (calculating the multipier in units of clock cycles rather
    #than time works out to be the same, so its all good.
    remainder = x % divisor
    #print 'remainder is ' + str(remainder)
    
    multiplier = numpy.floor(x/divisor)
    multiplier = int(multiplier)
    
    #print 'multiplier is ' + str(multiplier)    
    return multiplier, remainder

def test():
	
	#~ Sequence([(['mw'], 1.e8),
			  #~ ([], 1.e8)],loop=True)
    
    Sequence([(['ch1'], 100*ns),([], 100*ns),(['ch1'], 100*ns),([], 100*ns),(['ch1'], 100*ns),([], 100*ns),],loop=False)

#,(['ch1'], 10*us),([], 10*ns),(['ch1'], 10*us),([], 10*ns)
if __name__ == '__main__':
    #Light()
    test()
    #Night()
    #print factor(1023)
   
