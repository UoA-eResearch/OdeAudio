import sys
from threading import Semaphore

import numpy as np
from diffeqpy import de

from odes.equation import build_julia_dy


class JSolver:
    def __init__(self, y_init: np.array, args: np.array):
        self.dy = build_julia_dy()
        self.y_init = y_init

        self.args = args
        self.new_args = None

        self.step_size = 0.25

        self.solver = de.ODEProblem(self.dy, self.y_init, np.arange(0, 1000, self.step_size), self.args,
                                    abstol=1e-7, reltol=1e-7)

    change_args_sema = Semaphore()

    def change_args(self, *args):
        with self.change_args_sema:
            self.new_args = np.asarray(args)

    def solve(self, steps):
        # TODO
        pass

    def callback(self, outdata, frames, time, status):
        if status:
            print(status, file=sys.stderr)

