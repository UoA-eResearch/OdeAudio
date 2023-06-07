import numpy as np


@np.vectorize
def range_map(x0, x1, y0, y1, v):
    """Map a value v from one range [x0, x1] to another [y0, y1]"""
    return y0 + (y1 - y0) * (v - x0) / (x1 - x0)


def map_zip(x, y, x_from, x_to, y_from, y_to):
    return zip(
        range_map(*x_from, *x_to, x),
        range_map(*y_from, *y_to, y)
    )
