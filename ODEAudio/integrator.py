import sys
from threading import Thread

import numpy as np
from scipy.integrate import ode

from ODEAudio.odes.equation import dy, extract

import sounddevice as sd


class Integrator:
    def __init__(self, dy: callable, extract: callable, y_init: np.array, args: list):
        self.thread = None
        self.dy = dy
        self.extract = extract

        self.y_init = y_init
        self.args = args
        self.new_args = None

        self.t = 0
        self.y = y_init
        self.step_size = 5000
        self.start_index = 0
        self.buffer = 5000

        self.T = [0]
        self.Y = [y_init[1]]

        self.sample_freq = None
        self.dt = 0.25

        self.solver = ode(self.dy).set_integrator('vode', method='bdf', order=15, atol=1e-8, rtol=1e-8).\
            set_f_params(*self.args).set_initial_value(self.y_init)

    def prime(self):
        """Fill initial buffer and calculate constants"""
        self.integrate(self.step_size)

    def integrate(self, t_final):
        while self.solver.t < t_final:
            self.T.append(self.solver.t + self.dt)
            Y = self.solver.integrate(self.solver.t + self.dt)
            self.Y.append(2 * np.exp(Y[1]) - 0.5)

    def change_args(self, *args):
        self.new_args = args

    def thread_step(self):
        while True:
            if self.new_args:
                self.args = self.new_args
                self.new_args = None
                self.solver.set_f_params(*self.args)

            if len(self.Y) - self.buffer < self.start_index:
                self.T.append(self.solver.t + self.dt)
                Y = self.solver.integrate(self.solver.t + self.dt)
                self.Y.append(2 * np.exp(Y[1]) - 0.5)

            # if len(self.Y) > 100000:
            #     self.start_index -= len(self.Y) - 50000
            #     self.T = self.T[-50000:]
            #     self.Y = self.Y[-50000:]

    def start_thread(self):
        self.thread = Thread(target=self.thread_step)
        self.thread.start()

    def callback(self, outdata, frames, time, status):
        if status:
            print(status, file=sys.stderr)

        outdata[:, 0] = np.asarray(self.Y[self.start_index:self.start_index + frames])

        self.start_index += frames

        print(len(self.Y))


if __name__ == '__main__':
    I = Integrator(dy, extract, [-0.1, -0.101, -0.102], [1.001, 0.999])
    I.prime()
    I.start_thread()

    samplerate = sd.query_devices(None, 'output')['default_samplerate']
    with sd.OutputStream(device=None, channels=1, callback=I.callback, samplerate=samplerate/2,
                         blocksize=2000, latency=.3):
        input()
