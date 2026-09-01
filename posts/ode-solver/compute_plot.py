#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Dec  2 15:18:43 2024

@author: josh
"""

from matplotlib import pyplot as plt
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

### Computing Function ###
def compute(params, interval, h, bc):
  """
  The compute() function will run the numerical algorithm that returns a numpy
  array of values corresponding to each discretization point along x.
  Parameters:
  - params: list; Parameters p, q in the differential equation. Must be size 2.
  - interval: list; Points a, b to evaluate differential equation.
  - h: float; Size of discretization of x.
  - bc: list; Boundary conditions u(0), u(N) for N discrete points.
  Returns array.
  """
  ## Defining Parameters. ##
  p = params[0]
  q = params[1]
  a = interval[0]
  b = interval[1]
  u_0 = bc[0]
  u_N = bc[1]

  ## Setting up Space. i.e. Computing Discretization. ##
  # Number of points.
  pts = int((b-a)/h+1)
  # Discretization of x.
  x_space = np.linspace(0,1,pts)

  ## Setup Matrix Representation ##
  # Main diagonal.
  main_diag = [-(2/h**2 + (2*p)/(q+x_space[i])) for i in range(pts-2)]
  A1 = np.diag(main_diag)
  # Off-diagonal, left.
  off_diag_1 = [1/h**2 - 1/(h*(q+x_space[i])) for i in range(pts-3)]
  A2 = np.diag(off_diag_1,-1)
  # Off-diagonal, right.
  off_diag_0 = [1/h**2 + 1/(h*(q + x_space[i])) for i in range(pts-3)]
  A3 = np.diag(off_diag_0,1)
  # Matrix construction.
  A = A1 + A2 + A3

  ## Setup b Vector ##
  b = np.zeros(pts-2)
  # Boundary condition, left.
  b[0] = -(1/h**2 - 1/(h*(q+x_space[1]))) * u_0
  # Boundary condition, right.
  b[-1] = -(1/h**2 + 1/(h*(q+x_space[pts-1]))) * u_N

  ## Computing Solution ##
  x_calc = np.linalg.solve(A,b)
  # Add left boundary condition.
  x = np.insert(x_calc, 0, u_0)
  # Add right boundary condition.
  x = np.append(x, u_N)

  return [x_space, x]

### Testing h Function ###
def testing_h(params, interval, h_list, bc):
  """
  The testing_h() function will run the computation with varying values of
  h.
  Parameters:
  - params: list; Parameters p, q in the differential equation. Must be size 2.
  - interval: list; Points a, b to evaluate differential equation.
  - h: list; Varying sizes of discretization of x.
  - bc: list; Boundary conditions u(0), u(N) for N discrete points.
  """
  solutions_x = [compute(params, interval, h, bc) for h in h_list]
  return solutions_x

### Testing p,q functions ###
def testing_pq(params_p, params_q, interval, delta_x, bc):
  """
  The testing_pq() function will run the computation with varying parameters,
  p, q. For the function to work, ensure params_p and params_q aren't both
  lists of parameters. If params_p and params_q are both non-lists, then
  it will function like the compute() function before.
  Parameters:
  - params_p: list or int; Parameters p in the differential equation.
  - params_q: list or int; Parameters q in the differential equation.
  - interval: list; Points a, b to evaluate differential equation.
  - delta_x: int; Given discretization of x.
  - bc: list; Boundary conditions u(0), u(N) for N discrete points.
  """
  # If both p, q are lists of parameters.
  if (type(params_p) == list ) and (type(params_q) == list ):
    raise Exception("Ensure either p or q are not lists.")

  # If p is a list of parameters and q is not.
  elif (type(params_p) == list) and (type(params_q) != list):
    solutions_pq = [compute([p,params_q], interval, delta_x, bc) for p in params_p]
    return solutions_pq

  # If q is a list of parameters and p is not.
  elif (type(params_p) != list) and (type(params_q) == list):
    solutions_pq = [compute([params_p,q], interval, delta_x, bc) for q in params_q]
    return solutions_pq

  # Any other combination of data types.
  else:
    return compute([params_p, params_q], interval, delta_x, bc)


### Function for plotting parameters p, q ###
def parameter_plot(solutions, param_mod, param_list, param_static):
  """
  parameter_plot() will plot figures with sliders dependent on
  p, q as the list of varying parameters.
  Parameters:
  - solutions: list of np.array; Solutions of equations with
  space discretization. Compiled using the compute() function.
  - param_mod: str; Character for parameter to iterate over.
  Acceptable characters: "p", "q"
  - param_list: list; List of parameters to examine.
  - param_static: int or float; The constant parameter that does
  not change.
  """
  ### Creating figure for parameter p ###
  fig_B = go.Figure()

  ## Plotting Process for Varying p. $$
  if param_mod == "p":
    # Add traces.
    for step in range(len(param_list)):
      fig_B.add_trace(
        go.Scatter(
          visible = False,
          line = dict(color="#ff8000", width=3),
          name = "p = " + str(param_list[step]) + ", q = " + str(param_static),
          x = solutions[step][0],
          y = solutions[step][1]),
        )

    # Set default visible trace.
    fig_B.data[0].visible = True

    # Create slider.
    steps = []
    for i in range(len(fig_B.data)):
      step = dict(
        method="update",
        args=[{"visible": [False] * len(fig_B.data)},
              {"title": "Slider set p = " + str(param_list[i]) + ", q = " + str(param_static)}],  # layout attribute
      )
      step["args"][0]["visible"][i] = True  # Toggle i'th trace to "visible"
      steps.append(step)

    sliders = [dict(
      active=10,
      currentvalue={"prefix": "p = "},
      pad={"t": 50},
      steps=steps),
    ]

    fig_B.update_layout(
      sliders=sliders,
      width = 500, height = 500,
      yaxis=dict(
        title=dict(text="Solution, u(x)")
      ),

      xaxis=dict(
        title=dict(text="Point along Rod, x")
      )
    )

    return fig_B

  ## Plotting Process for Varying q ##
  elif param_mod == "q":
    # Add traces.
    for step in range(len(param_list)):
      fig_B.add_trace(
        go.Scatter(
          visible = False,
          line = dict(color="#ff8000", width=3),
          name = "p = " + str(param_static) + ", q = " + str(param_list[step]),
          x = solutions[step][0],
          y = solutions[step][1]),
        )

    # Set default visible trace.
    fig_B.data[0].visible = True

    # Create slider.
    steps = []
    for i in range(len(fig_B.data)):
      step = dict(
        method="update",
        args=[{"visible": [False] * len(fig_B.data)},
              {"title": "Slider set p = " + str(param_static) + ", q = " + str(param_list[i])}],  # layout attribute
      )
      step["args"][0]["visible"][i] = True  # Toggle i'th trace to "visible"
      steps.append(step)

    sliders = [dict(
      active=10,
      currentvalue={"prefix": "q = "},
      pad={"t": 50},
      steps=steps),
    ]

    fig_B.update_layout(
      sliders=sliders,
      width = 500, height = 500,
      yaxis=dict(
        title=dict(text="Solution, u(x)")
      ),

      xaxis=dict(
          title=dict(text="Point along Rod, x")
      )
    )

    return fig_B

  else:
    raise Exception("Invalid string. Must be 'p' or 'q'.")