import julia
import numpy as np

julia.Julia()


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


def dy5(_, y, cA, eA, cB, eB):

    y2exp = np.exp(2 * y)

    ytot = y2exp.sum()

    vec_evals = np.asarray([-cA, eB, -cB, eA, 0])

    dy = np.asarray([
        1 - ytot + np.dot(np.roll(y2exp, -(i + 1)), vec_evals)
        for i in range(len(y))
    ])

    return dy


def dy5_vec(_, y, cA, eA, cB, eB):

    y2exp = np.exp(2 * y)

    ytot = y2exp.sum(axis=0)

    vec_evals = np.asarray([-cA, eB, -cB, eA, 0])

    dy = np.asarray([
        1 - ytot + np.dot(vec_evals, np.roll(y2exp, -(i + 1), axis=0))
        for i in range(len(y))
    ])

    return dy


def build_julia_dy():
    return julia.Main.eval("""
        using LinearAlgebra
        
        function du(u, p, t)
            u[u .> 0] .= 0
            u[u .== -Inf] .= -1000
        
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
