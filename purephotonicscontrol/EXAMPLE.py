import ITLA_Wrap
import time

if __name__ == "__main__":                            
    
    ITLA = ITLA_Wrap.ITLA_Class(port="COM6",baudrate=9600)
     
    #Probe laser and check it's happy
    ITLA.ProbeLaser()
    
    #Laser is happier if we set all the parameters when it's off
    ITLA.EnableLaser(False)
    
##     ITLA.SetFrequency(194.9412)
##     
##     ITLA.SetSweepRange(140)
    
##     ITLA.SetSweepRate(6500)
##     
##     ITLA.SetPower(1600)
##     
##     ITLA.EnableLaser(True)
##     # do science

##     ITLA.EnableWhisperMode(True)

##     time.sleep(1)

##     ITLA.EnableSweep(True)

##     time.sleep(2)


    #turn everything off
##     ITLA.EnableSweep(False)
##     ITLA.EnableWhisperMode(False)
##     ITLA.EnableLaser(False)
    
##     ITLA.SetFrequency(194.942)
##     ITLA.EnableLaser(True)
##     ITLA.EnableWhisperMode(True)
##     
##     time.sleep(2)
##     ITLA.EnableWhisperMode(False)
##     ITLA.EnableLaser(False)
    ITLA.sercon.close()