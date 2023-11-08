import numpy as np


def backfill_nans(data):
    """Replace all nans with the last valid value"""
    mask = np.isnan(data)
    idx = np.where(~mask, np.arange(mask.shape[0]).reshape(-1, 1), 0)
    np.maximum.accumulate(idx, axis=0, out=idx)
    data[mask] = data[idx[mask], np.nonzero(mask)[1]]


def smooth_pops(data):
    """Detects sharp changes in signal, and spreads those changes over a few samples"""
    for i in range(data.shape[1]):
        diff = np.diff(data[:, i])
        for j in range(2, len(diff)-2):
            if abs(diff[j]) > 0.5:
                diff[j-2] += 0.2 * diff[j]
                diff[j-1] += 0.2 * diff[j]
                diff[j+1] += 0.2 * diff[j]
                diff[j+2] += 0.2 * diff[j]
                diff[j] *= 0.2
        data[:, i] = np.cumsum(np.insert(diff, 0, data[0, i]))
