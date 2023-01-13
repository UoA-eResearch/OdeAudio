from threading import Thread

import sounddevice as sd


def audio_stream(callback: callable):
    samplerate = sd.query_devices(None, 'output')['default_samplerate']
    stream = sd.OutputStream(device=None, channels=1,
                             callback=callback, samplerate=samplerate/2,
                             blocksize=2000, latency=.1)

    stream.start()


def thread_stream(callback: callable) -> Thread:
    thread = Thread(target=audio_stream, args=[callback])
    thread.start()
    return thread
