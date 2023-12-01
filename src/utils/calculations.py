
import numpy as np



def mean_ci(array, return_ci=True, axis=0, n_rounding=None):
    """Computes the mean of array and optionally returns 95% confidence
    interval. array can be vector or multi-dimensional array, in which case it
    computes means and confidence intervas across the specified axis. Confidence intervals are returned on the form: mean, lower, upper."""
    avg = np.nanmean(array, axis=axis)

    if return_ci is True:
        n_samples = np.shape(array)[axis]
        stdev_estimator = np.nanstd(array, axis=axis)/np.sqrt(n_samples)
        ci_lower = avg - stdev_estimator*1.96
        ci_upper = avg + stdev_estimator*1.96
        if n_rounding:
            avg = avg.round(n_rounding)
            ci_lower = ci_lower.round(n_rounding)
            ci_upper = ci_upper.round(n_rounding)
        return {
            "mean": avg,
            "lower": ci_lower,
            "upper": ci_upper,
        }
    return avg