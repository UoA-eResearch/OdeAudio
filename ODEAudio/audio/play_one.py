import numpy as np
import sounddevice
from scipy.fft import fft
from scipy.interpolate import interp1d

from ODEAudio.odes.gen_sequence import gen_sequence


def make_sound(T, Y):
    # Extract and interpolate data
    yy = Y[1, :]
    yc = 2 * (np.exp(yy) - 0.5)

    tdiff = T[-1] / len(T)
    tnew = np.arange(0, T[-1], tdiff)

    interp = interp1d(T, yc)
    ynew = interp(tnew)

    # Find mean frequency
    Nx = len(tnew)
    if Nx % 2 != 0:
        tnew = tnew[0:-1]
        ynew = ynew[0:-1]
        Nx = len(tnew)

    # Fourier transform
    qq = fft(ynew)
    P2 = np.abs(qq / Nx)
    P1 = P2[0:int(Nx/2 + 1)]
    P1[1:-2] = 2 * P1[1:-2]

    Fs = 1 / tdiff
    TT = 1 / Fs

    omega = Fs * (np.arange(0, Nx/2 + 1)) / Nx
    mean_omega = sum(omega * P1) / sum(P1)

    mf = 500
    freq_scale = mean_omega / mf

    new_sample_freq = Fs / freq_scale

    sounddevice.play(ynew, new_sample_freq, blocking=True)


if __name__ == '__main__':
    T, Y = gen_sequence()
    make_sound(T, Y)