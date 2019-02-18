
import ps5000a
import matplotlib.pyplot as plt
import numpy as np
import time

ps = ps5000a.PS5000a()
try:
	ps.setChannel(channel="B", coupling="DC", VRange=0.1)
	ps.setChannel(channel="A", enabled=False)

	n_captures = 3
	sample_interval = 1e-9  # 100 ns
	sample_duration = 10e-6  # 1 ms
	ps.setResolution('8')
	ps.setSamplingInterval(sample_interval, sample_duration)
	ps.setSimpleTrigger("B", threshold_V=0.01, timeout_ms=1)

	samples_per_segment = ps.memorySegments(n_captures)
	samples_per_segment = int(sample_duration/sample_interval +100)

	ps.setNoOfCaptures(n_captures)
	
	data = np.zeros((n_captures, samples_per_segment), dtype=np.int16)

	t1 = time.time()

	ps.runBlock()
	ps.waitReady()

	t2 = time.time()
	print("Time to record data to scope: ", str(t2 - t1))

	ps.getDataRawBulk(data=data, channel='B')

	t3 = time.time()
	print("Time to copy to RAM: ", str(t3 - t2))




finally:
	ps.close()
