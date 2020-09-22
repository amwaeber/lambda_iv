import numpy as np
from scipy import optimize
from scipy.optimize import OptimizeWarning
import warnings

warnings.simplefilter("error", OptimizeWarning)


def fit_iv(df):

    isc, disc = fit_isc(df)
    voc, dvoc = fit_voc(df)
    pmax = fit_pmax(df)

    return [isc, disc, voc, dvoc, pmax]


def fit_isc(df, n_points=3, m0=-1e-2):
    isc_idx = df.index[df['Voltage (V)'].abs() == df['Voltage (V)'].abs().min()][0]
    slice_df = df[0:isc_idx + max(isc_idx, n_points)]

    try:
        popt, pcov = optimize.curve_fit(lambda x, y0, m: y0 + m * x,
                                        slice_df['Voltage (V)'],
                                        slice_df['Current (A)'],
                                        p0=np.array([slice_df['Current (A)'][0], m0]))
    except OptimizeWarning:
        return [-1, -1]
    return [popt[0] * 1e3, np.sqrt(np.diag(pcov))[0] * 1e3]


def fit_voc(df, n_points=5, y00=1, a0=1, b0=1):
    voc_idx = df.index[df['Current (A)'].abs() == df['Current (A)'].abs().min()][0]
    slice_df = df[voc_idx - n_points:voc_idx + n_points]

    try:
        popt, pcov = optimize.curve_fit(lambda x, y0, a, b: y0 + a * x + b * x ** 2,
                                        slice_df['Current (A)'],
                                        slice_df['Voltage (V)'],
                                        p0=np.array([y00, a0, b0]))
    except OptimizeWarning:
        return [-1, -1]
    return [popt[0] * 1e3, np.sqrt(np.diag(pcov))[0] * 1e3]


def fit_pmax(df, n_points=10, i00=4e-5, vt0=7.5e-2):
    df['Power (W)'] = df['Current (A)'] * df['Voltage (V)']
    if any(df['Current (A)'] > 0):
        pmax = df.loc[df['Current (A)'] > 0]['Power (W)'].max()
    else:
        pmax = 0

    pmax_idx = df.index[df['Power (W)'] == pmax][0]
    slice_df = df[pmax_idx - n_points:pmax_idx + n_points]

    def shockley(v, iph, i0, vt):
        return iph - i0 * np.exp(v / vt)

    try:
        popt, pcov = optimize.curve_fit(shockley,
                                        slice_df['Voltage (V)'],
                                        slice_df['Current (A)'],
                                        p0=np.array([df['Current (A)'][0], i00, vt0]))
        voltage_pmax = optimize.minimize_scalar(lambda v: - v * shockley(v, *popt)).x
    except OptimizeWarning:
        return -1
    return voltage_pmax * shockley(voltage_pmax, *popt) *1e3
