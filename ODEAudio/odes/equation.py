import numpy as np


def dy(_, y, lambda_c, lambda_e):
    """derivative function for GH  cycle"""

    y2exp = np.exp(2 * y)

    y_tot = y2exp.sum()

    dy = np.asarray([
        1 - y_tot - lambda_c * y2exp[1] + lambda_e * y2exp[2],
        1 - y_tot - lambda_c * y2exp[2] + lambda_e * y2exp[0],
        1 - y_tot - lambda_c * y2exp[0] + lambda_e * y2exp[1],
    ])

    return dy


def extract(t, y):
    yc = 2 * (np.exp(y[1, :]) - 0.5)
    return t, yc