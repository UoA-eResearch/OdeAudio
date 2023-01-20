from threading import Thread

import sounddevice as sd


class AudioStream:
    def __init__(self, callback: callable):
        self.callback = callback
        self.running = False
        self.samplerate = sd.query_devices(None, 'output')['default_samplerate']
        self.stream = sd.OutputStream(device=None, channels=1,
                                      callback=callback, samplerate=self.samplerate/2,
                                      blocksize=2000, latency=.1)

    def start(self):
        self.stream.start()

    def pause(self):
        if self.stream.stopped:
            self.stream.start()
        else:
            self.stream.stop()

    def close(self):
        self.stream.close()
