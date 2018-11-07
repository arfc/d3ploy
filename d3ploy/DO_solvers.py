"""
This file manages Deterministic-optimizing libaries for the D3ploy cyclus modules.

"""
import numpy as np

def polyfit_regression(ts, back_steps=10, degree=1):
    """
    Fits a polynomial to the entries in timeseries [ts]
    to predict the next value.

    Parameters:
    -----------
    ts: Array of floats
        An array of times series data to be used for the polyfit regression
    backsteps: int
        Number of backsteps to fit. (default=all past data)
    degree: int
        Degree of the fitting polynomial
    Returns:
    --------
    x : The predicted value from the fit polynomial.
    """
    time = range(1, len(ts) + 1)
    timeseries = np.array(list(ts.values()))
    fit = np.polyfit(time[-back_steps:],
                     timeseries[-back_steps:], deg=degree)
    eq = np.poly1d(fit)
    x = eq(len(ts) + 1)
    return x
