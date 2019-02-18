## Test: Pulse Blaster
import pulse_blaster_Milos as pb
import time

s = 1
ms = 10**-3
us = 10**-6
ns = 10**-9


pb.Sequence([(['ch1'],1*s),([],1*s),
    (['ch1'],1*s),([],1*s),
    (['ch1'],1*s),([],1*s),
    (['ch1'],1*s),([],1*s),
    (['ch1'],1*s),([],1*s)],
    loop=False)