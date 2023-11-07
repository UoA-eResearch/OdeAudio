import sounddevice as sd

# Performance tuning parameters
# - Sample rate:    how many data points (per second) to play as sound
#                   lower means lower pitch, but also less data to process
#                   higher means higher pitch, but more performance issues
sample_rate = 1300  # If None, uses the device default
# - Block size:     how many data points the sound driver requests at a time
#                   not sure if this has a performance impact
block_size = 500
# - Latency:        when to request new data - i.e.: how many seconds of data the driver has left when it requests more
#                   higher values increase the input latency, but reduce instability
latency = 0.2


class AudioStream:
    def __init__(self, callback: callable):
        self.callback = callback
        self.running = False
        self.samplerate = sd.query_devices(None, 'output')['default_samplerate']
        if sample_rate is not None:
            self.samplerate = sample_rate
        self.stream = sd.OutputStream(device=None, channels=2,
                                      callback=callback, samplerate=self.samplerate,
                                      blocksize=block_size, latency=latency)

    def start(self):
        self.stream.start()

    def pause(self):
        if self.stream.stopped:
            self.stream.start()
        else:
            self.stream.stop()

    def close(self):
        self.stream.close()
