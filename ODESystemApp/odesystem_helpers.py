from __future__ import division
__author__ = 'benjamin'

import scipy.integrate
import numpy as np


# all imports have to be done using absolute imports -> that's a bug of bokeh which is know and will be fixed.
def import_bokeh(relative_path):
    import imp
    import os
    app_root_dir = os.path.dirname(os.path.realpath(__file__))
    return imp.load_source('', app_root_dir + '/' + relative_path)


# import local modules
odesystem_settings = import_bokeh('odesystem_settings.py')


def parser(fun_str):
    from sympy import sympify, lambdify
    from sympy.abc import x,y

    fun_sym = sympify(fun_str)
    fun_lam = lambdify([x, y], fun_sym)
    return fun_lam, fun_sym


def do_integration(x0, y0, u, v, bounds, chaotic):
    f = lambda t,x:[u(x[0], x[1]), v(x[0], x[1])]
    init = [x0,y0]
    t0 = 0

    backend = 'vode'

    solver = scipy.integrate.ode(f).set_integrator(backend)
    solver.set_initial_value(init, t0)

    sol = [[x0,y0]]
    x, y = sol[-1]

    x_min = bounds['x_min']
    x_max = bounds['x_max']
    y_min = bounds['y_min']
    y_max = bounds['y_max']

    n_step = 0

    res = (x_max - x_min) / (odesystem_settings.n_sample-1) * .1
    dx = 10*res
    dy = 10*res

    while x_min <= x <= x_max and y_min <= y <= y_max and \
                    n_step < odesystem_settings.streamline_integration_steps and \
            (dx > .1 * res or dy > .1 * res or chaotic):
        df = max([abs(u(x, y)), abs(v(x, y))])
        dt = res / df * 2
        solver.integrate(solver.t + dt)
        dx = abs(x - solver.y[0])
        dy = abs(y - solver.y[1])
        x,y = solver.y
        sol.append([x, y])
        n_step += 1
        print n_step

    sol = np.array(sol)

    return sol[:,0].tolist(), sol[:,1].tolist()


def critical_points(u_sym, v_sym, bounds):
    import sympy
    from sympy.abc import x,y
    repeat = True
    x_c = []
    y_c = []
    x_lines=[]
    y_lines=[]
    while repeat:
        u_sym = u_sym.simplify()
        v_sym = v_sym.simplify()
        system = (u_sym, v_sym)
        s=sympy.solve(system, (x,y),dict=True)
        repeat = False
        print "system:"
        print system
        print "solutions:"
        print s

        for solution in s:
            vars =  solution.keys()
            if x in vars and y in vars:
                x_sol = solution[x]
                y_sol = solution[y]
                if x_sol.is_real and y_sol.is_real:
                    print "found pt:"
                    print solution
                    real_point = True

                    if u_sym.subs(x,x_sol).is_zero and v_sym.subs(x,x_sol).is_zero:
                        print "pt is actually a line!"
                        print "x = %d" % float(x_sol)
                        u_sym = u_sym / (x_sol - x)
                        v_sym = v_sym / (x_sol - x)
                        l_y = sympy.lambdify(y,x_sol)
                        y_lines.append(l_y)
                        repeat = True
                        real_point = False
                    if u_sym.subs(y,y_sol).is_zero and v_sym.subs(y,y_sol).is_zero:
                        print "pt is actually a line!"
                        print "y = %d" % float(y_sol)
                        u_sym = u_sym / (y_sol - y)
                        v_sym = v_sym / (y_sol - y)
                        l_x = sympy.lambdify(x,y_sol)
                        x_lines.append(l_x)
                        repeat = True
                        real_point = False
                    if real_point:
                        x_c.append(float(x_sol))
                        y_c.append(float(y_sol))


            elif y in vars:
                repeat = True
                l_x = sympy.lambdify(x,solution[y])
                u_sym = u_sym / (solution[y] - y)
                v_sym = v_sym / (solution[y] - y)
                x_lines.append(l_x)
                print "found xline:"
                print solution
            elif x in vars:
                repeat = True
                l_y = sympy.lambdify(y,solution[x])
                u_sym = u_sym / (solution[x] - x)
                v_sym = v_sym / (solution[x] - x)
                y_lines.append(l_y)
                print "found yline:"
                print solution
            else:
                print "no pts found"

    x_val_lines = [[]]
    y_val_lines = [[]]

    h = get_stepwidth(bounds)

    for x_line in x_lines:
        x_val_line = np.arange(bounds['x_min'],bounds['x_max'],h * .1).tolist()
        y_val_line = []
        for x_val in x_val_line:
            y_val_line.append(x_line(x_val))
        x_val_lines.append(x_val_line)
        y_val_lines.append(y_val_line)

    for y_line in y_lines:
        x_val_line = []
        y_val_line = np.arange(bounds['y_min'],bounds['y_max'],h * .1).tolist()
        for y_val in y_val_line:
            x_val_line.append(y_line(y_val))
        x_val_lines.append(x_val_line)
        y_val_lines.append(y_val_line)

    return x_c, y_c, x_val_lines, y_val_lines


def get_stepwidth(bounds):
    return (bounds['x_max'] - bounds['x_min']) / (odesystem_settings.n_sample - 1)


def critical_points_iso(u_sym, v_sym, bounds):
    from sympy.abc import x,y
    from sympy import lambdify

    potential = lambdify([x,y],u_sym**2+v_sym**2)

    x_min = bounds['x_min']
    x_max = bounds['x_max']
    y_min = bounds['y_min']
    y_max = bounds['y_max']

    h = get_stepwidth(bounds)

    [x,y] = np.meshgrid(np.arange(x_min,x_max,h),np.arange(y_min,y_max,h))

    samples = potential(x,y)

    x_c = x[abs(samples)<10**-6]
    y_c = y[abs(samples)<10**-6]

    return x_c, y_c



