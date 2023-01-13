import numpy as np
from scipy.integrate import solve_ivp, ode

from ODEAudio.odes.equation import dy


def gen_sequence():
    y_init = np.array([-0.1, -0.101, -0.102])

    t_fin = 50000

    sol = solve_ivp(dy, [0, t_fin], y_init, rtol=1e-8, atol=1e-8, args=[1.001, 0.999], method='RK45')

    return sol.t, sol.y


def gen_sequence2():
    y_init = np.array([-0.1, -0.101, -0.102])

    t_fin = 50000
    dt = 0.25
    n = int(t_fin / dt)

    solver = ode(dy).set_integrator('vode', method='bdf', atol=1e-8, rtol=1e-8).set_f_params(1.001, 0.999).\
        set_initial_value(y_init)

    y = np.zeros((3, n+1))
    t = np.zeros((n+1,))
    t[0] = 0
    y[:, 0] = y_init
    i = 1
    while solver.t < t_fin:
        t[i] = solver.t + dt
        y[:, i] = solver.integrate(solver.t + dt)
        i += 1

    return t, y
