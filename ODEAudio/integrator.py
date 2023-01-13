import sys
from threading import Thread, Semaphore

import numpy as np
from scipy.integrate import ode
from sounddevice import sleep

from ODEAudio.odes.equation import dy, extract

from audio.play_stream import thread_stream
from utility.buffer import Buffer


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

        t, y = self.extract(0, np.asarray(y_init).reshape(-1, 1))

        self.T = Buffer(100000)
        self.T.append(0)

        self.Y = Buffer(100000)
        self.Y.append(y[0])

        self.YY = Buffer(100000)
        self.YY.append(y_init)

        self.sample_freq = None
        self.dt = 0.25

        self.solver = ode(self.dy).set_integrator('vode', method='bdf', order=15, atol=1e-7, rtol=1e-7).\
            set_f_params(*self.args).set_initial_value(self.y_init)

    def prime(self):
        """Fill initial buffer and calculate constants"""
        self.integrate(self.step_size)

    def integrate(self, t_final):
        while self.solver.t < t_final:
            self.T.append(self.solver.t + self.dt)
            Y = self.solver.integrate(self.solver.t + self.dt)
            self.YY.append(Y)
            self.Y.append(2 * np.exp(Y[1]) - 0.5)

    change_args_sema = Semaphore()

    def change_args(self, *args):
        with self.change_args_sema:
            self.new_args = tuple(args)

    def thread_step(self):
        while True:
            with self.change_args_sema:
                if self.new_args:
                    self.args = self.new_args
                    self.new_args = None
                    self.solver.set_f_params(*self.args)
                    self.solver.set_initial_value(self.YY[self.start_index], self.T[self.start_index])
                    self.T.truncate(self.start_index)
                    self.Y.truncate(self.start_index)
                    self.YY.truncate(self.start_index)

            if self.Y.last_index() - self.buffer < self.start_index:
                self.T.append(self.solver.t + self.dt)
                Y = self.solver.integrate(self.solver.t + self.dt)
                self.YY.append(Y)
                self.Y.append(2 * np.exp(Y[1]) - 0.5)

    def start_thread(self):
        self.thread = Thread(target=self.thread_step)
        self.thread.start()

    def callback(self, outdata, frames, time, status):
        if status:
            print(status, file=sys.stderr)

        while self.Y.last_index() < self.start_index + frames:
            sleep(10)

        outdata[:, 0] = np.asarray(self.Y[self.start_index:self.start_index + frames])

        self.start_index += frames


if __name__ == '__main__':
    I = Integrator(dy, extract, [-0.1, -0.101, -0.102], [1.001, 0.999])
    I.prime()
    I.start_thread()

    sound = thread_stream(I.callback)
