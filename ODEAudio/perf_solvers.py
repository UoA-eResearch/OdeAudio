import numpy as np
from scipy.integrate import ode, solve_ivp, BDF
from scipy.interpolate import interp1d
import matplotlib.pyplot as plt
from ODEAudio.odes.equation import dy5_vec as dy
from time import perf_counter
from tqdm import tqdm
import julia
from diffeqpy import de
import seaborn as sns

julia.Julia()

ode_methods = [
    ('vode', 'adams'),
    ('vode', 'bdf'),
    # ('zvode', 'adams'),
    # ('zvode', 'bdf'),
    ('lsoda', 'adams'),
    ('lsoda', 'bdf'),
    'dopri5',
    'dop853'
]

solve_ivp_methods = [
    'RK45',
    'RK23',
    'DOP853',
    # 'Radau',
    # 'BDF',
    'LSODA'
]


def plots(results, title, time_x):
    plt.figure()
    plt.title(title)
    for label, res in results.items():
        plt.plot(time_x, res[2], label=label)
    plt.legend()

    plt.figure()
    plt.title(f'{title} trace')
    for label, res in results.items():
        plt.plot(res[0], res[1], label=label)
        # plt.plot(res[0], np.abs(np.subtract(res[1], control[1][:len(res[1])])), label=label)
    plt.legend()


def gen_ivp_fixed(method, dy, y_init, args, t_steps, atol, rtol, step_size=None):
    yy = y_init
    t_out = []
    y_out = []
    times = []
    for tt in t_steps:
        steps = int(1 + ((tt[1] - tt[0]) / step_size))
        t_eval = np.linspace(tt[0], tt[1], steps)

        start = perf_counter()
        sol = solve_ivp(dy, tt, yy, t_eval=t_eval, args=args, method=method, rtol=rtol, atol=atol, vectorized=vectorized)
        time = perf_counter() - start

        t_out.extend(sol.t)
        y_out.extend(sol.y[0, :])
        times.append(time / sol.y.shape[1])

        yy = sol.y[:, -1]

    return t_out, y_out, times


def gen_ivp_interp(method, dy, y_init, args, t_steps, atol, rtol, step_size=None):
    yy = y_init
    t_out = []
    y_out = []
    times = []
    for tt in t_steps:
        start = perf_counter()
        sol = solve_ivp(dy, tt, yy, args=args, method=method, rtol=rtol, atol=atol, vectorized=vectorized)

        # Interpolate
        y = sol.y
        t = sol.t
        if step_size is None:
            # Regular steps, but the same number as generated
            t_new = np.linspace(t[0], t[-1], len(t))
        else:
            # Regular steps at the specified interval
            t_new = np.arange(t[0], t[-1], step_size)
        interp = interp1d(t, y[0, :])   # Note - take only one dimension of Y
        y_new = interp(t_new)
        time = perf_counter() - start

        t_out.extend(t_new)
        y_out.extend(y_new)
        times.append(time / len(y_new))

        yy = sol.y[:, -1]

    return t_out, y_out, times


def gen_sol(method, dy, y_init, args, t_steps, atol, rtol, step_size=1.0):
    solver = ode(dy)
    if isinstance(method, tuple):
        solver.set_integrator(method[0], method=method[1], atol=atol, rtol=rtol)
    else:
        solver.set_integrator(method, atol=atol, rtol=rtol)

    solver.set_f_params(*args)
    solver.set_initial_value(y_init)

    t_out = []
    y_out = []
    times = []

    for tt in t_steps:
        start = perf_counter()
        while solver.t < tt[1]:
            t_out.append(solver.t + step_size)
            y = solver.integrate(solver.t + step_size)
            y_out.append(y[0])
        time = perf_counter() - start
        times.append(time / ((tt[1] - tt[0]) / step_size))

    return t_out, y_out, times


jul_f = julia.Main.eval("""
using LinearAlgebra

function du(u, p, t)
    u2exp = exp.(2*u)
    utot = sum(u2exp)

    cA, eA, cB, eB = p

    vecs = [-cA, eB, -cB, eA, 0]

    return [
        1 - utot + dot(circshift(u2exp, -i), vecs)
        for i in 1:5
            ]
end
""")


def gen_julia(method, dy, y_init, args, t_steps, atol, rtol, step_size=1.0):
    t_out = np.asarray([0])
    y_out = np.asarray([y_init]).T
    times = []

    yy = np.asarray(y_init)

    prob = de.ODEProblem(jul_f, yy, np.asarray(t_steps[0]), np.asarray(args),
                         abstol=atol, reltol=rtol)

    for tt in t_steps:
        start = perf_counter()

        subp = de.remake(prob, u0=yy, tspan=np.asarray(tt)) #, tspan=np.asarray(tt))
        sol = de.solve(subp)

        t_new = np.arange(tt[0], tt[-1], step_size)
        y_new = np.asarray(sol(t_new))
        # print(np.asarray(y_new).shape)
        t_out = np.hstack((t_out, t_new))
        y_out = np.hstack((y_out, y_new))

        yy = np.asarray(sol.u[-1])

        time = perf_counter() - start
        times.append(time / ((tt[1] - tt[0]) / step_size))

    return t_out, y_out, times


# y_init = [-.1, -.101, -.102]
y_init = [-.1, -.101, -.102, -.103, -.104]
# lambdas = [1.001, 0.999]
lambdas = [1.001, 0.999, 1.002, 0.998]
vectorized = True


def plot_method_speeds():
    t_starts = np.arange(0, 20000, 1000)
    t_steps = [[i, i+1000] for i in t_starts]
    err_tol = 1e-6

    interp_results = {
        meth: gen_ivp_interp(meth, dy, y_init, lambdas, t_steps, err_tol, err_tol, step_size=.25)
        for meth in tqdm(solve_ivp_methods, desc='IVP with interpolation')
    }

    plots(interp_results, 'IVP interpolation', t_starts)

    fixed_results = {
        meth: gen_ivp_fixed(meth, dy, y_init, lambdas, t_steps, err_tol, err_tol, step_size=.25)
        for meth in tqdm(solve_ivp_methods, desc='IVP with fixed step')
    }

    plots(fixed_results, 'IVP fixed step', t_starts)

    solver_results = {
        meth: gen_sol(meth, dy, y_init, lambdas, t_steps, err_tol, err_tol, step_size=.25)
        for meth in tqdm(ode_methods, desc='Solver')
    }

    plots(solver_results, 'solver', t_starts)

    julia_results = {
        'julia': gen_julia(None, None, y_init, lambdas, t_steps, err_tol, err_tol, step_size=0.25)
    }

    sns.lineplot(data=julia_results['julia'][1].T)

    # plots(julia_results, 'Julia', t_starts)

    plt.show()


def plot_accuracy_speeds(method, sol_methods):
    t_starts = np.arange(0, 20000, 1000)
    t_steps = [[i, i + 1000] for i in t_starts]
    err_tols = [10**-x for x in range(1, 8)]
    err_tol = 1e-7

    step_sizes = [0.25, 0.5, 0.75, 1]
    step_size = 0.25

    control = gen_ivp_fixed('RK45', dy, y_init, lambdas, t_steps, 1e-8, 1e-8, .25)

    interp_results = {
        step_size: gen_ivp_interp(method, dy, y_init, lambdas, t_steps, err_tol, err_tol, step_size=step_size)
        for step_size in tqdm(step_sizes, desc='IVP with interpolation')
    }

    plots(interp_results, 'IVP interpolation', t_starts)

    # plt.show()

    fixed_results = {
        step_size: gen_ivp_fixed(method, dy, y_init, lambdas, t_steps, err_tol, err_tol, step_size=step_size)
        for step_size in tqdm(step_sizes, desc='IVP with fixed step')
    }

    plots(fixed_results, 'IVP fixed step', t_starts)

    solver_results = {
        step_size: gen_sol(method, dy, y_init, lambdas, t_steps, err_tol, err_tol, step_size=step_size)
        for step_size in tqdm(step_sizes, desc='Solver')
    }

    plots(solver_results, 'solver', t_starts)

    plt.show()


if __name__ == '__main__':
    plot_method_speeds()
    # plot_accuracy_speeds('LSODA', [])
