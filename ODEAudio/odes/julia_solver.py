import sys

import numpy as np
from diffeqpy import de
from sounddevice import sleep

from odes.equation import build_julia_dy
from utility.pop_filter import backfill_nans, smooth_pops
from utility.trace import Trace


# Performance tuning parameters
# - Buffer size:    bigger means we request larger integration chunks from julia,
#                   more efficient, but more likely to hitch when we truncate the buffer
#                   (prime numbers may help avoid integration aligning with output boundary)
buffer_size = 3013
# - Step size:      smaller means we get more data points for a given t range,
#                   stretching out the signal and reducing pitch
#                   this may be a cheap way to get more data for less integration,
#                   but it's probably more effective to reduce the sample rate (play_stream.py)
step_size = 0.5
# - Init dt:        the initial dt used by the integrator - larger may mean better performance, or it may be
#                   quickly overriden by the integrator and have no effect at all
init_dt = step_size / 8
# - Truncation buffer: how much data to keep when the parameter values change
#                   larger means less hitching, but a longer delay until you hear the parameter change
truncation_buffer = 1517
#


class JSolver:
    def __init__(self, y_init: np.array, args: np.array):
        self.dy = build_julia_dy()
        self.y_init = y_init
        self.yy = y_init
        self.new_init = None

        self.channels = [0, 1]

        self.args = args
        self.new_args = None        # Receive new parameters
        self.flush_buffer = False   # On generating new data, overwrite the buffer rather than extending it

        self.update_freq = False    # Flag to update the frequency plot

        self.step_size = step_size

        self.solver = de.ODEProblem(self.dy, self.y_init, (0, 250), self.args,
                                    abstol=1e-7, reltol=1e-7)

        self.trace_file = Trace()
        self.trace_file.update_pars(*self.args)

        self.buffer = buffer_size

        self.start_index = 0
        self.Y = self.y_init

    def start_thread(self):
        pass

    def close(self):
        self.trace_file.close()

    def reset(self, y_init):
        self.new_init = y_init
        self.trace_file.close()
        self.trace_file = Trace()

    def change_args(self, *args):
        self.new_args = np.asarray(args)

    def thread_step(self):
        buf = self.buffer

        if self.new_args is not None:
            self.args = self.new_args
            self.new_args = None

            # Trim the buffer (not completely), then schedule new generation from there
            self.flush_buffer = True
            # Avoid buffer aligning with callback
            end_index = min(self.Y.shape[0]-1, self.start_index + truncation_buffer)
            self.yy = np.log((self.Y[end_index, :]/2)+0.5)
            self.Y = self.Y[self.start_index:end_index, :]
            self.start_index = 0

            self.trace_file.update_pars(*self.args)

        if self.new_init is not None:
            self.y_init = self.new_init
            self.yy = self.new_init
            self.new_init = None

            self.Y = self.yy
            self.start_index = 0

        if len(self.Y) - buf < self.start_index or self.flush_buffer:
            prob = de.remake(self.solver,
                             u0=self.yy,
                             tspan=(0, 2 * buf * self.step_size),
                             p=self.args,
                             dt=init_dt
                             )
            sol = de.solve(prob)
            t_out = np.arange(0, 2 * buf * self.step_size, self.step_size)

            self.yy = sol.u[-1]
            y = np.asarray(sol(t_out))

            out = 2 * (np.exp(y.T) - 0.5)

            # Pop filtering (all disabled for now as probably not necessary)
            # backfill_nans(out)
            # smooth_pops(out)

            self.Y = np.vstack((self.Y, out))
            self.Y = self.Y[self.start_index:, :]
            self.start_index = 0
            self.flush_buffer = False

            # self.trace_file.write(t_out, y.T)

    def get_trace(self):
        pts = 2000
        if self.Y.shape[0] < pts \
                or self.Y.shape[0] < self.start_index \
                or self.new_args is not None \
                or self.new_init is not None:
            self.update_freq = False
            return None

        self.update_freq = False

        data = self.Y[self.start_index - pts:self.start_index]

        if data.shape[0] < pts:
            return None

        return np.linspace(0, 1, data.shape[0]), np.exp(data)

    def get_frequency(self):
        pts = 2000
        if self.Y.shape[0] < pts\
                or self.Y.shape[0] < self.start_index\
                or self.new_args is not None\
                or self.new_init is not None:
            self.update_freq = False
            return None

        self.update_freq = False

        # Offset mean
        data = self.Y[self.start_index-pts:self.start_index]
        data = data - np.mean(data, axis=0)

        if data.shape[0] < pts:
            return None

        # Calc frequencies
        spectrum = abs(np.fft.fftshift(
            np.fft.fft(data, axis=0)
        ))

        freq = np.fft.fftshift(
            np.fft.fftfreq(pts)
        )

        # Take only the positive half
        x = freq[pts//2:100 + pts//2]
        y = spectrum[pts//2:100 + pts//2]

        # Scale to 0-1
        x /= np.amax(x, axis=0)
        y /= np.amax(y, axis=0)

        # Create points list
        return x, y

    def set_channel(self, input, output):
        self.channels[output] = input

    def callback(self, outdata, frames, time, status):
        if status:
            print(status, file=sys.stderr)

        while len(self.Y) < self.start_index + frames:
            sleep(10)

        d = np.asarray(self.Y[self.start_index:self.start_index + frames, self.channels])

        outdata[:, :] = d # 2 * (np.exp(d) - 0.5)

        # Trace the actual data being played - this has a huge performance cost
        # self.trace_file.write(np.arange(0, frames), outdata)

        self.start_index += frames
        self.update_freq = True

