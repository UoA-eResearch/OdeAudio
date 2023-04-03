import sys

import numpy as np
from diffeqpy import de
from sounddevice import sleep

from odes.equation import build_julia_dy


class JSolver:
    def __init__(self, y_init: np.array, args: np.array):
        self.dy = build_julia_dy()
        self.y_init = y_init
        self.yy = y_init
        self.new_init = None

        self.args = args
        self.new_args = None

        self.step_size = 0.25

        self.solver = de.ODEProblem(self.dy, self.y_init, (0, 250), self.args,
                                    abstol=1e-7, reltol=1e-7)

        self.buffer = 10000

        self.start_index = 0
        self.Y = np.asarray([[0, 0]])

    def start_thread(self):
        pass

    def close(self):
        pass

    def reset(self, y_init):
        self.new_init = y_init

    def change_args(self, *args):
        self.new_args = np.asarray(args)

    def thread_step(self):
        buf = self.buffer

        if self.new_args is not None:
            self.args = self.new_args
            self.new_args = None

            self.Y = self.yy[:2]
            self.start_index = 0

        if self.new_init is not None:
            self.y_init = self.new_init
            self.yy = self.new_init
            self.new_init = None

            self.Y = self.yy[:2]
            self.start_index = 0

        if len(self.Y) - buf < self.start_index:
            prob = de.remake(self.solver,
                             u0=self.yy,
                             tspan=(0, 2 * buf * self.step_size),
                             p=self.args
                             )
            sol = de.solve(prob)
            t_out = np.arange(0, 2 * buf * self.step_size, self.step_size)

            self.yy = sol.u[-1]
            y = np.asarray(sol(t_out))
            self.Y = np.vstack((self.Y, y[:2, :].T))

    def callback(self, outdata, frames, time, status):
        if status:
            print(status, file=sys.stderr)

        while len(self.Y) < self.start_index + frames:
            self.buffer = 10 * frames
            sleep(10)

        outdata[:, :] = np.asarray(self.Y[self.start_index:self.start_index + frames, :2])

        self.start_index += frames

